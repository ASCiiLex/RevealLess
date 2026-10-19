from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from narrative.models import Obra, Personaje, ProgresoUsuario, UnidadNarrativa
from posts.models import Post
from subscriptions.models import Suscripcion
from subscriptions.services import crear_suscripcion, filtro_posts_suscripciones


def _unidades(obra, total):
    unidades = [
        UnidadNarrativa.objects.create(obra=obra, tipo='episodio', nombre=f'E{i}', orden_local=i)
        for i in range(1, total + 1)
    ]
    obra.recalcular_orden()
    for unidad in unidades:
        unidad.refresh_from_db()
    return unidades


class PersonajeBase(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('lectora', password='x')
        self.autor = User.objects.create_user('autor', password='x')
        self.client.force_login(self.usuario)

        self.serie = Obra.objects.create(titulo='Serie', slug='serie')
        self.pelicula = Obra.objects.create(titulo='Película', slug='pelicula')
        self.e1, self.e2 = _unidades(self.serie, 2)
        (self.p1,) = _unidades(self.pelicula, 1)

        self.personaje = Personaje.objects.create(nombre='Heroína')
        self.personaje.unidades.add(self.e2, self.p1)

    def _progreso(self, unidad):
        ProgresoUsuario.objects.create(
            usuario=self.usuario, obra=unidad.obra, unidad_actual=unidad, orden_absoluto=unidad.orden_fin,
        )

    def _post(self, unidad, etiquetado=False):
        post = Post.objects.create(
            author=self.autor, obra=unidad.obra, text='x',
            referencia_narrativa=unidad, frontera_spoiler=unidad, frontera_origen='explicito',
        )
        if etiquetado:
            post.personajes.add(self.personaje)
        return post


class PersonajeLandingTests(PersonajeBase):
    def _landing(self):
        return self.client.get(reverse('narrative_api_personaje_landing', args=[self.personaje.id]))

    def test_sin_aparicion_alcanzada_da_404(self):
        self._progreso(self.e1)
        self.assertEqual(self._landing().status_code, 404)

    def test_solo_lista_obras_con_la_aparicion_alcanzada(self):
        self._progreso(self.e2)
        datos = self._landing().json()
        self.assertEqual([o['slug'] for o in datos['obras']], ['serie'])

    def test_refleja_la_suscripcion(self):
        self._progreso(self.e2)
        suscripcion = crear_suscripcion(self.usuario, personaje=self.personaje)
        datos = self._landing().json()
        self.assertEqual(datos['suscripcion_id'], suscripcion.id)
        self.assertEqual(datos['total_suscriptores'], 1)

    def test_la_vista_react_monta_la_landing(self):
        response = self.client.get(reverse('narrative_personaje_landing', args=[self.personaje.id]))
        self.assertContains(response, f'data-personaje-id="{self.personaje.id}"')

    def test_la_landing_de_obra_incluye_la_suscripcion_del_personaje(self):
        self._progreso(self.e2)
        suscripcion = crear_suscripcion(self.usuario, personaje=self.personaje)
        datos = self.client.get(reverse('narrative_api_obra_landing', args=[self.serie.slug])).json()
        self.assertEqual(datos['personajes'][0]['suscripcion_id'], suscripcion.id)


class PersonajeFeedTests(PersonajeBase):
    def setUp(self):
        super().setUp()
        self._progreso(self.e2)
        crear_suscripcion(self.usuario, obra=self.serie)

    def test_filtra_solo_por_etiqueta(self):
        """Anclarse a una unidad donde aparece no basta: el post tiene que etiquetarlo."""
        self._post(self.e2)
        self._post(self.e1)
        etiquetado = self._post(self.e1, etiquetado=True)

        response = self.client.get(reverse('narrative_api_feed'), {'personaje': self.personaje.id})
        ids = {p['id'] for p in response.json()['results']}
        self.assertEqual(ids, {etiquetado.id})

    def test_personaje_no_numerico_da_400(self):
        response = self.client.get(reverse('narrative_api_feed'), {'personaje': 'abc'})
        self.assertEqual(response.status_code, 400)

    def test_la_suscripcion_solo_incluye_posts_etiquetados(self):
        Suscripcion.objects.filter(usuario=self.usuario).delete()
        sin_etiqueta = self._post(self.e2)
        etiquetado = self._post(self.e2, etiquetado=True)
        crear_suscripcion(self.usuario, personaje=self.personaje)

        ids = set(Post.objects.filter(filtro_posts_suscripciones(self.usuario)).values_list('id', flat=True))
        self.assertEqual(ids, {etiquetado.id})
        self.assertNotIn(sin_etiqueta.id, ids)