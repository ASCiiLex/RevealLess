from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from follows.models import Follow
from likes.models import PostReaction
from comments.models import Comment
from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from posts.models import Post


class FeedAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.usuario = User.objects.create_user('usuario_api', password='x')
        self.seguido = User.objects.create_user('seguido_api', password='x')
        self.desconocido = User.objects.create_user('desconocido_api', password='x')

        Follow.objects.create(follower=self.usuario, followed=self.seguido)

        self.obra = Obra.objects.create(titulo='Serie API', slug='serie-api')
        self.e1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E1', orden_local=1)
        self.e2 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E2', orden_local=2)
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()

        actualizar_progreso(self.usuario, self.obra, self.e1)
        actualizar_progreso(self.seguido, self.obra, self.e1)

        # Post propio, con frontera por delante del propio progreso del usuario.
        self.post_propio = Post.objects.create(
            author=self.usuario, obra=self.obra, text='mi post adelantado',
            referencia_narrativa=self.e1, frontera_spoiler=self.e2,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        # Post de un seguido, visible con el progreso actual del usuario.
        self.post_seguido_visible = Post.objects.create(
            author=self.seguido, obra=self.obra, text='post seguido visible',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        # Post de un seguido, no visible (frontera por delante del progreso del usuario).
        self.post_seguido_no_visible = Post.objects.create(
            author=self.seguido, obra=self.obra, text='post seguido con spoiler',
            referencia_narrativa=self.e1, frontera_spoiler=self.e2,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        # Post de alguien no seguido: no debe aparecer aunque sea visible.
        self.post_desconocido = Post.objects.create(
            author=self.desconocido, obra=self.obra, text='post ajeno',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

        PostReaction.objects.create(user=self.seguido, post=self.post_propio, reaction='like')
        Comment.objects.create(
            user=self.seguido, post=self.post_propio, text='comentario',
            referencia_narrativa=self.e1,
        )

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('narrative_api_feed'))
        self.assertEqual(response.status_code, 403)

    def test_incluye_post_propio_aunque_no_visible_para_si_mismo(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertIn(self.post_propio.id, ids)

    def test_incluye_post_de_seguido_visible(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertIn(self.post_seguido_visible.id, ids)

    def test_excluye_post_de_seguido_no_visible(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertNotIn(self.post_seguido_no_visible.id, ids)

    def test_excluye_post_de_no_seguido(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        ids = [p['id'] for p in response.data['results']]
        self.assertNotIn(self.post_desconocido.id, ids)

    def test_todos_los_posts_incluyen_likes_count_y_comments_count(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        for post_data in response.data['results']:
            self.assertIn('likes_count', post_data)
            self.assertIn('comments_count', post_data)

    def test_post_propio_refleja_conteos_correctos(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        post_data = next(p for p in response.data['results'] if p['id'] == self.post_propio.id)
        self.assertEqual(post_data['likes_count'], 1)
        self.assertEqual(post_data['comments_count'], 1)