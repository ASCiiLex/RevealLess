from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import Obra, Personaje, UnidadNarrativa
from narrative.services import actualizar_progreso
from ..models import Post
from .utils import crear_obra, crear_post


def _obra_con_arcos(slug):
    """Dos arcos de dos episodios: posiciones 1-2 y 3-4."""
    obra = Obra.objects.create(titulo=slug, slug=slug)
    arcos = [
        UnidadNarrativa.objects.create(obra=obra, tipo='arco', nombre=f'Arco {n}', orden_local=n)
        for n in (1, 2)
    ]
    episodios = [
        UnidadNarrativa.objects.create(
            obra=obra, padre=arcos[i // 2], tipo='episodio', nombre=f'E{i + 1}', orden_local=i % 2 + 1,
        )
        for i in range(4)
    ]
    obra.recalcular_orden()
    for unidad in arcos + episodios:
        unidad.refresh_from_db()
    return obra, arcos, episodios


def _personaje(nombre, unidad):
    personaje = Personaje.objects.create(nombre=nombre)
    personaje.unidades.add(unidad)
    return personaje


class FronteraMinimaCrearTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('autor_frontera_minima', password='x')
        self.obra, self.eps = crear_obra('frontera-minima', 3)
        actualizar_progreso(self.autor, self.obra, self.eps[0])
        self.client.force_authenticate(user=self.autor)

    def _publicar(self, obra, **datos):
        return self.client.post(reverse('posts_api_create', args=[obra.slug]), {'text': 'x', **datos})

    def test_frontera_anterior_a_la_referencia_se_eleva(self):
        response = self._publicar(self.obra, referencia_narrativa=self.eps[1].id, frontera_spoiler=self.eps[0].id)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Post.objects.get(id=response.data['id']).frontera_spoiler, self.eps[1])

    def test_frontera_posterior_a_la_referencia_se_respeta(self):
        response = self._publicar(self.obra, referencia_narrativa=self.eps[0].id, frontera_spoiler=self.eps[2].id)
        self.assertEqual(Post.objects.get(id=response.data['id']).frontera_spoiler, self.eps[2])

    def test_referencia_de_bloque_exige_su_primer_episodio(self):
        obra, arcos, eps = _obra_con_arcos('frontera-minima-arcos')
        actualizar_progreso(self.autor, obra, eps[0])
        response = self._publicar(obra, referencia_narrativa=arcos[1].id, frontera_spoiler=eps[0].id)
        self.assertEqual(Post.objects.get(id=response.data['id']).frontera_spoiler, eps[2])


class FronteraMinimaEdicionTests(TestCase):
    def test_editar_a_una_frontera_anterior_a_la_referencia_la_eleva(self):
        autor = User.objects.create_user('editor_frontera_minima', password='x')
        obra, eps = crear_obra('frontera-minima-edicion', 2)
        post = crear_post(autor, obra, eps[1])

        cliente = APIClient()
        cliente.force_authenticate(user=autor)
        response = cliente.patch(
            reverse('posts_api_update', args=[post.id]), {'frontera_spoiler': eps[0].id}, format='multipart',
        )
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.frontera_spoiler, eps[1])


class FronteraCruzadaPorPersonajeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('autor_cruzada_personaje', password='x')
        self.anime, self.eps = crear_obra('anime-cruzada-personaje', 2)
        self.manga, self.caps = crear_obra('manga-cruzada-personaje', 3, tipo_unidad='capitulo', tipo=Obra.TIPO_MANGA)
        actualizar_progreso(self.autor, self.anime, self.eps[0])
        self.luffy = _personaje('Luffy', self.eps[0])
        self.zoro = _personaje('Zoro', self.eps[1])
        self.shanks = _personaje('Shanks', self.caps[1])
        self.client.force_authenticate(user=self.autor)

    def _publicar(self, comparados):
        return self.client.post(
            reverse('posts_api_create', args=[self.anime.slug]),
            {
                'text': 'comparativa',
                'referencia_narrativa': self.eps[0].id,
                'frontera_spoiler': self.eps[0].id,
                'obra_cruzada': self.manga.id,
                'personajes_comparados': [p.id for p in comparados],
            },
            format='multipart',
        )

    def test_sin_parte_de_la_otra_obra_usa_la_primera_aparicion(self):
        response = self._publicar([self.luffy, self.shanks])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Post.objects.get(id=response.data['id']).frontera_cruzada, self.caps[1])

    def test_sin_parte_ni_personaje_de_la_otra_obra_devuelve_400(self):
        response = self._publicar([self.luffy, self.zoro])
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Post.objects.exists())


class SugerirFronteraMinimaTests(TestCase):
    def test_la_sugerencia_no_queda_por_debajo_de_la_referencia(self):
        autor = User.objects.create_user('autor_sugerir_minima', password='x')
        obra, eps = crear_obra('sugerir-minima', 2)
        actualizar_progreso(autor, obra, eps[0])
        cliente = APIClient()
        cliente.force_authenticate(user=autor)

        propuesta = SimpleNamespace(frontera_spoiler=eps[0], parte=None, confianza=0.9, es_utilizable=True)
        with patch('posts.api_views.sugerir.proponer_clasificacion', return_value=propuesta):
            response = cliente.post(
                f'/posts/api/sugerir-frontera/{obra.slug}/',
                {'text': 'algo', 'referencia_narrativa': eps[1].id},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['frontera']['id'], eps[1].id)