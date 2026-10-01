from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import ClasificacionNarrativa, Obra, Personaje, UnidadNarrativa
from ..models import Post


class PostUpdateAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('editor_post', password='x')
        self.otro_usuario = User.objects.create_user('otro_editor_post', password='x')

        self.obra = Obra.objects.create(titulo='Serie Editar Post', slug='serie-editar-post')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='texto original',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def _editar(self, datos, usuario=None):
        self.client.force_authenticate(user=usuario or self.autor)
        return self.client.patch(reverse('posts_api_update', args=[self.post.id]), datos)

    def test_requiere_autenticacion(self):
        response = self.client.patch(
            reverse('posts_api_update', args=[self.post.id]), {'text': 'nuevo'},
        )
        self.assertEqual(response.status_code, 403)

    def test_solo_el_autor_puede_editar(self):
        self.assertEqual(self._editar({'text': 'intento ajeno'}, self.otro_usuario).status_code, 403)

    def test_edita_el_texto(self):
        self.assertEqual(self._editar({'text': 'texto editado'}).status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, 'texto editado')

    def test_editar_frontera_marca_origen_explicito(self):
        self._editar({'frontera_spoiler': self.e2.id})
        self.post.refresh_from_db()
        self.assertEqual(self.post.frontera_spoiler, self.e2)
        self.assertEqual(self.post.frontera_origen, ClasificacionNarrativa.ORIGEN_EXPLICITO)

    def test_sin_enviar_frontera_no_se_modifica(self):
        """Decision explicita: omitir frontera_spoiler en la edicion NO
        dispara recalculo con IA (a diferencia de la creacion) -- se
        interpreta como 'sin cambios'."""
        frontera_original = self.post.frontera_spoiler
        origen_original = self.post.frontera_origen

        self._editar({'text': 'solo cambio el texto'})
        self.post.refresh_from_db()
        self.assertEqual(self.post.frontera_spoiler, frontera_original)
        self.assertEqual(self.post.frontera_origen, origen_original)

    def test_devuelve_404_si_el_post_no_existe(self):
        self.client.force_authenticate(user=self.autor)
        response = self.client.patch(
            reverse('posts_api_update', args=[999999]), {'text': 'x'},
        )
        self.assertEqual(response.status_code, 404)

    def test_edicion_parcial_no_requiere_todos_los_campos(self):
        self.assertEqual(self._editar({'nivel_spoiler': 'importante'}).status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.nivel_spoiler, 'importante')
        self.assertEqual(self.post.text, 'texto original')

    def test_edita_emocion_autor(self):
        self.assertEqual(self._editar({'emocion_autor': 'me_entristece'}).status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.emocion_autor, 'me_entristece')

    def test_editar_el_texto_reetiqueta_personajes(self):
        nami = Personaje.objects.create(nombre='Nami')
        nami.unidades.add(self.e1)
        self._editar({'text': 'Nami roba el mapa'})
        self.assertEqual(list(self.post.personajes.all()), [nami])

    def test_bajar_la_frontera_retira_personajes_posteriores(self):
        kuro = Personaje.objects.create(nombre='Kuro')
        kuro.unidades.add(self.e2)
        self._editar({'text': 'Kuro trama algo', 'frontera_spoiler': self.e2.id})
        self.assertEqual(list(self.post.personajes.all()), [kuro])
        self._editar({'frontera_spoiler': self.e1.id})
        self.assertFalse(self.post.personajes.exists())