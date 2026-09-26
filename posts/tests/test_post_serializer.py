from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from likes.models import PostReaction
from narrative.services import actualizar_progreso
from .utils import crear_obra, crear_post


class FeedUserReactionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('feed_reactor', password='x')
        obra, (e1,) = crear_obra('serie-feed-reaction')
        actualizar_progreso(self.usuario, obra, e1)
        self.post = crear_post(self.usuario, obra, e1, text='post con reaccion')
        self.client.force_authenticate(user=self.usuario)

    def _post_en_feed(self):
        response = self.client.get(reverse('narrative_api_feed'))
        return next(p for p in response.data['results'] if p['id'] == self.post.id)

    def test_feed_incluye_user_reaction_none_sin_reaccionar(self):
        self.assertIsNone(self._post_en_feed()['user_reaction'])

    def test_feed_incluye_user_reaction_correcta(self):
        PostReaction.objects.create(user=self.usuario, post=self.post, reaction='funny')
        self.assertEqual(self._post_en_feed()['user_reaction'], 'funny')


class PostSerializerIsOwnPostTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('is_own_autor', password='x')
        self.otro = User.objects.create_user('is_own_otro', password='x')
        obra, (e1,) = crear_obra('serie-is-own')
        actualizar_progreso(self.autor, obra, e1)
        actualizar_progreso(self.otro, obra, e1)
        self.url = reverse('posts_api_detail', args=[crear_post(self.autor, obra, e1).id])

    def test_is_own_post_true_para_el_autor(self):
        self.client.force_authenticate(user=self.autor)
        self.assertTrue(self.client.get(self.url).data['post']['is_own_post'])

    def test_is_own_post_false_para_otro_usuario(self):
        self.client.force_authenticate(user=self.otro)
        self.assertFalse(self.client.get(self.url).data['post']['is_own_post'])

    def test_is_own_post_false_para_anonimo(self):
        """El anónimo ni siquiera ve el post (404): 'anónimo != autor' se resuelve antes del serializer."""
        self.assertEqual(self.client.get(self.url).status_code, 404)


class PostSerializerFronteraSpoilerTests(TestCase):
    def test_incluye_frontera_spoiler_completa(self):
        client = APIClient()
        autor = User.objects.create_user('frontera_serializer_autor', password='x')
        obra, (e1, e2) = crear_obra('serie-frontera-serializer', 2)
        actualizar_progreso(autor, obra, e2)
        post = crear_post(autor, obra, e1, frontera=e2)

        client.force_authenticate(user=autor)
        frontera = client.get(reverse('posts_api_detail', args=[post.id])).data['post']['frontera_spoiler']
        self.assertEqual(frontera['id'], e2.id)
        self.assertIn('orden_inicio', frontera)