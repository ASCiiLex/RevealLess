from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from follows.models import Follow
from narrative.models import Obra, TemaTransversal
from narrative.services import actualizar_progreso, asegurar_unidad_previa
from posts.tests.utils import crear_obra, crear_post
from subscriptions.models import Suscripcion
from subscriptions.services import crear_suscripcion


class FeedDescubrirTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('lector_desc', password='x')
        self.seguido = User.objects.create_user('seguido_desc', password='x')
        self.desconocido = User.objects.create_user('desconocido_desc', password='x')
        Follow.objects.create(follower=self.usuario, followed=self.seguido)

        # Obra con progreso pero sin suscripción.
        self.obra, (self.u1, self.u2, self.u3) = crear_obra('descubrir-progreso', n=3)
        actualizar_progreso(self.usuario, self.obra, self.u2)
        self.ajena, (self.a1,) = crear_obra('descubrir-ajena')
        self.estreno = Obra.objects.create(titulo='Estreno', slug='descubrir-estreno')
        self.previa = asegurar_unidad_previa(self.estreno)

        self.client.force_authenticate(user=self.usuario)

    def _ids(self, vista='descubrir', **params):
        response = self.client.get(reverse('narrative_api_feed'), {'vista': vista, **params})
        self.assertEqual(response.status_code, 200)
        return [p['id'] for p in response.data['results']]

    def test_vista_invalida_devuelve_400(self):
        response = self.client.get(reverse('narrative_api_feed'), {'vista': 'todo'})
        self.assertEqual(response.status_code, 400)

    def test_incluye_post_ajeno_dentro_de_mi_progreso(self):
        post = crear_post(self.desconocido, self.obra, self.u2)
        self.assertIn(post.id, self._ids())
        self.assertNotIn(post.id, self._ids('biblioteca'))

    def test_excluye_post_ajeno_por_delante_de_mi_progreso(self):
        post = crear_post(self.desconocido, self.obra, self.u3)
        self.assertNotIn(post.id, self._ids())

    def test_incluye_previa_de_obra_sin_progreso(self):
        post = crear_post(self.desconocido, self.estreno, self.previa)
        self.assertIn(post.id, self._ids())

    def test_excluye_obra_sin_progreso_fuera_de_la_previa(self):
        post = crear_post(self.desconocido, self.ajena, self.a1)
        self.assertNotIn(post.id, self._ids())

    def test_excluye_propios_y_de_seguidos(self):
        propio = crear_post(self.usuario, self.obra, self.u1)
        de_seguido = crear_post(self.seguido, self.estreno, self.previa)

        descubrir = self._ids()
        biblioteca = self._ids('biblioteca')
        self.assertNotIn(propio.id, descubrir)
        self.assertNotIn(de_seguido.id, descubrir)
        self.assertIn(propio.id, biblioteca)
        self.assertIn(de_seguido.id, biblioteca)

    def test_lo_que_llega_por_suscripcion_pasa_a_biblioteca(self):
        post = crear_post(self.desconocido, self.obra, self.u1)
        crear_suscripcion(self.usuario, self.obra)
        self.assertNotIn(post.id, self._ids())
        self.assertIn(post.id, self._ids('biblioteca'))

    def test_excluye_el_alcance_silenciado(self):
        tema = TemaTransversal.objects.create(obra=self.obra, nombre='Tema silenciado')
        crear_suscripcion(self.usuario, self.obra, tema=tema)
        Suscripcion.objects.filter(usuario=self.usuario, tema=tema).update(activa=False)

        post = crear_post(self.desconocido, self.obra, self.u1)
        post.temas_transversales.set([tema])
        self.assertNotIn(post.id, self._ids())

    def test_filtra_por_obra(self):
        de_obra = crear_post(self.desconocido, self.obra, self.u1)
        de_estreno = crear_post(self.desconocido, self.estreno, self.previa)

        ids = self._ids(obra=self.estreno.id)
        self.assertIn(de_estreno.id, ids)
        self.assertNotIn(de_obra.id, ids)


class FeedPaginacionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('lector_pag', password='x')
        self.autor = User.objects.create_user('autor_pag', password='x')
        estreno = Obra.objects.create(titulo='Estreno paginado', slug='paginacion-estreno')
        previa = asegurar_unidad_previa(estreno)
        self.ajenos = [crear_post(self.autor, estreno, previa, text=f'ajeno {i}') for i in range(13)]
        self.propios = [crear_post(self.usuario, estreno, previa, text=f'propio {i}') for i in range(13)]
        self.client.force_authenticate(user=self.usuario)

    def _recorrer(self, vista):
        response = self.client.get(reverse('narrative_api_feed'), {'vista': vista})
        self.assertNotIn('count', response.data)
        primera = [p['id'] for p in response.data['results']]
        self.assertEqual(len(primera), 12)
        self.assertIsNotNone(response.data['next'])

        segunda = self.client.get(response.data['next'])
        resto = [p['id'] for p in segunda.data['results']]
        self.assertIsNone(segunda.data['next'])
        return primera, resto

    def test_descubrir_pagina_por_cursor_sin_repetir(self):
        primera, resto = self._recorrer('descubrir')
        self.assertEqual(len(resto), 1)
        self.assertEqual(set(primera) | set(resto), {p.id for p in self.ajenos})
        self.assertEqual(primera[0], self.ajenos[-1].id)

    def test_biblioteca_pagina_por_cursor_sin_repetir(self):
        primera, resto = self._recorrer('biblioteca')
        self.assertEqual(len(resto), 1)
        self.assertEqual(set(primera) | set(resto), {p.id for p in self.propios})