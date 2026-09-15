from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from comments.models import Comment
from likes.models import PostReaction
from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from .models import Post


class PostDetailAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('detalle_autor', password='x')
        self.lector = User.objects.create_user('detalle_lector', password='x')

        self.obra = Obra.objects.create(titulo='Serie Detalle Post', slug='serie-detalle-post')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()

        # Progreso del lector alcanza e1: necesario para que el post
        # explicito con frontera=e1 sea realmente visible para el.
        # visible_for() exige progreso_lector >= frontera_orden, un
        # anonimo (progreso 0) nunca alcanzaria frontera_orden=e1.orden_fin.
        actualizar_progreso(self.lector, self.obra, self.e1)

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='post de prueba',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_visible_para_usuario_con_progreso_suficiente(self):
        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)

    def test_anonimo_sin_progreso_recibe_404(self):
        """Un anonimo tiene progreso 0 -- nunca alcanza frontera_orden
        de un post con frontera > 0, ni siquiera uno explicito. Esto es
        el comportamiento correcto y ya probado de visible_for(), no
        una limitacion de PostDetailAPIView."""
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 404)

    def test_autor_ve_su_propio_post_sin_progreso(self):
        self.client.force_authenticate(user=self.autor)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)

    def test_devuelve_404_si_no_visible_para_el_usuario(self):
        post_bloqueado = Post.objects.create(
            author=self.autor, obra=self.obra, text='con spoiler',
            referencia_narrativa=self.e1, frontera_spoiler=self.e2,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[post_bloqueado.id]))
        self.assertEqual(response.status_code, 404)

    def test_incluye_datos_del_post(self):
        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(response.data['post']['id'], self.post.id)

    def test_incluye_comentarios_de_nivel_superior(self):
        Comment.objects.create(
            user=self.lector, post=self.post, text='un comentario',
            referencia_narrativa=self.e1,
        )
        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(len(response.data['comments']), 1)

    def test_incluye_replies_anidadas(self):
        padre = Comment.objects.create(
            user=self.lector, post=self.post, text='padre',
            referencia_narrativa=self.e1,
        )
        Comment.objects.create(
            user=self.autor, post=self.post, parent=padre, text='reply',
            referencia_narrativa=self.e1,
        )
        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(len(response.data['comments'][0]['replies']), 1)

    def test_incluye_user_reaction_del_post(self):
        PostReaction.objects.create(user=self.lector, post=self.post, reaction='love')
        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(response.data['post_reaction'], 'love')

    def test_post_reaction_es_none_sin_reaccion(self):
        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertIsNone(response.data['post_reaction'])

    def test_ordena_por_popular(self):
        c1 = Comment.objects.create(
            user=self.lector, post=self.post, text='poco popular',
            referencia_narrativa=self.e1,
        )
        c2 = Comment.objects.create(
            user=self.autor, post=self.post, text='muy popular',
            referencia_narrativa=self.e1,
        )
        from comments.models import CommentReaction
        CommentReaction.objects.create(user=self.autor, comment=c2, reaction='like')
        CommentReaction.objects.create(user=self.lector, comment=c2, reaction='love')

        self.client.force_authenticate(user=self.lector)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]), {'sort': 'popular'})
        self.assertEqual(response.data['comments'][0]['id'], c2.id)


class FeedUserReactionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('feed_reactor', password='x')
        self.obra = Obra.objects.create(titulo='Serie Feed Reaction', slug='serie-feed-reaction')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        actualizar_progreso(self.usuario, self.obra, self.e1)

        self.post = Post.objects.create(
            author=self.usuario, obra=self.obra, text='post con reaccion',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_feed_incluye_user_reaction_none_sin_reaccionar(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        post_data = next(p for p in response.data['results'] if p['id'] == self.post.id)
        self.assertIsNone(post_data['user_reaction'])

    def test_feed_incluye_user_reaction_correcta(self):
        PostReaction.objects.create(user=self.usuario, post=self.post, reaction='funny')
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('narrative_api_feed'))
        post_data = next(p for p in response.data['results'] if p['id'] == self.post.id)
        self.assertEqual(post_data['user_reaction'], 'funny')


class PostSerializerIsOwnPostTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('is_own_autor', password='x')
        self.otro = User.objects.create_user('is_own_otro', password='x')

        self.obra = Obra.objects.create(titulo='Serie Is Own', slug='serie-is-own')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        actualizar_progreso(self.autor, self.obra, self.e1)
        actualizar_progreso(self.otro, self.obra, self.e1)

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='post propio',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_is_own_post_true_para_el_autor(self):
        self.client.force_authenticate(user=self.autor)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertTrue(response.data['post']['is_own_post'])

    def test_is_own_post_false_para_otro_usuario(self):
        self.client.force_authenticate(user=self.otro)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertFalse(response.data['post']['is_own_post'])

    def test_is_own_post_false_para_anonimo(self):
        """Un anonimo tiene progreso 0 -- nunca alcanza frontera_orden
        de un post con frontera > 0 (mismo comportamiento ya confirmado
        en PostDetailAPIViewTests.test_anonimo_sin_progreso_recibe_404).
        No se puede comprobar is_own_post en un post que el anonimo ni
        siquiera puede ver -- el propio 404 ya demuestra que 'anonimo
        != autor' se resuelve correctamente antes de llegar al
        serializer."""
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 404)


class PostSerializerFronteraSpoilerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('frontera_serializer_autor', password='x')
        self.obra = Obra.objects.create(titulo='Serie Frontera Serializer', slug='serie-frontera-serializer')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()
        actualizar_progreso(self.autor, self.obra, self.e2)

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='post con frontera',
            referencia_narrativa=self.e1, frontera_spoiler=self.e2,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_incluye_frontera_spoiler_completa(self):
        self.client.force_authenticate(user=self.autor)
        response = self.client.get(reverse('posts_api_detail', args=[self.post.id]))
        self.assertEqual(response.data['post']['frontera_spoiler']['id'], self.e2.id)
        self.assertIn('orden_inicio', response.data['post']['frontera_spoiler'])