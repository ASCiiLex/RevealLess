from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.models import ClasificacionNarrativa, Obra
from narrative.services import actualizar_progreso
from posts.models import Hashtag, Post
from posts.tests.utils import crear_obra
from ..models import Comment

HEREDADO = ClasificacionNarrativa.ORIGEN_HEREDADO_POST
EXPLICITO = ClasificacionNarrativa.ORIGEN_EXPLICITO


class RebajarFronteraTests(TestCase):
    """El autor del post decide sobre lo suyo, no sobre lo que otros comentaron para la frontera anterior."""

    def setUp(self):
        self.obra, self.eps = crear_obra('serie-herencia', 3)
        self.autor = User.objects.create_user('autor_herencia', password='x')
        self.comentarista = User.objects.create_user('comentarista_herencia', password='x')
        self.lector = User.objects.create_user('lector_herencia', password='x')
        actualizar_progreso(self.autor, self.obra, self.eps[2])
        actualizar_progreso(self.comentarista, self.obra, self.eps[2])
        actualizar_progreso(self.lector, self.obra, self.eps[1])
        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='post',
            referencia_narrativa=self.eps[0], frontera_spoiler=self.eps[2], frontera_origen=EXPLICITO,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.autor)

    def _comentar(self, usuario, texto='comentario'):
        return Comment.objects.create(
            user=usuario, post=self.post, text=texto,
            referencia_narrativa=self.eps[0], frontera_origen=HEREDADO,
        )

    def _editar(self, **datos):
        respuesta = self.client.patch(reverse('posts_api_update', args=[self.post.id]), datos, format='multipart')
        self.assertEqual(respuesta.status_code, 200)

    def test_bajar_la_frontera_no_destapa_comentarios_ajenos(self):
        comentario = self._comentar(self.comentarista)
        self._editar(frontera_spoiler=self.eps[1].id)

        self.assertIn(self.post, Post.objects.visible_for(self.lector))
        self.assertNotIn(comentario, Comment.objects.visible_for(self.lector))
        comentario.refresh_from_db()
        self.assertEqual((comentario.frontera_spoiler, comentario.frontera_origen), (self.eps[2], EXPLICITO))

    def test_los_comentarios_del_autor_del_post_siguen_la_nueva_frontera(self):
        propio = self._comentar(self.autor)
        self._editar(frontera_spoiler=self.eps[1].id)

        propio.refresh_from_db()
        self.assertEqual(propio.frontera_origen, HEREDADO)
        self.assertIn(propio, Comment.objects.visible_for(self.lector))

    def test_subir_la_frontera_no_toca_los_comentarios(self):
        self.post.frontera_spoiler = self.eps[1]
        self.post.save()
        comentario = self._comentar(self.comentarista)
        self._editar(frontera_spoiler=self.eps[2].id)

        comentario.refresh_from_db()
        self.assertEqual(comentario.frontera_origen, HEREDADO)

    def test_bajar_la_frontera_retira_los_hashtags_de_los_comentarios_ajenos(self):
        self._comentar(self.comentarista, 'giro final #muereace')
        self._editar(frontera_spoiler=self.eps[1].id)

        self.assertNotIn('muereace', Hashtag.objects.visibles_para(self.lector).values_list('name', flat=True))


class RebajarFronteraCruzadaTests(TestCase):
    def setUp(self):
        self.anime, self.eps = crear_obra('anime-herencia', 2)
        self.manga, self.caps = crear_obra('manga-herencia', 3, tipo_unidad='capitulo', tipo=Obra.TIPO_MANGA)
        self.autor = User.objects.create_user('autor_cruzada_herencia', password='x')
        comentarista = User.objects.create_user('comentarista_cruzada_herencia', password='x')
        for usuario in (self.autor, comentarista):
            actualizar_progreso(usuario, self.anime, self.eps[1])
            actualizar_progreso(usuario, self.manga, self.caps[2])
        self.post = Post.objects.create(
            author=self.autor, obra=self.anime, text='comparativa',
            referencia_narrativa=self.eps[0], frontera_spoiler=self.eps[0], frontera_origen=EXPLICITO,
            obra_cruzada=self.manga, frontera_cruzada=self.caps[2], modo_cruce=Post.MODO_COMPARATIVA,
        )
        self.comentario = Comment.objects.create(
            user=comentarista, post=self.post, text='comentario',
            referencia_narrativa=self.eps[0], frontera_origen=HEREDADO,
        )

    def test_bajar_la_frontera_cruzada_conserva_la_anterior_en_los_comentarios(self):
        lector = User.objects.create_user('lector_cruzada_herencia', password='x')
        actualizar_progreso(lector, self.anime, self.eps[1])
        actualizar_progreso(lector, self.manga, self.caps[0])

        cliente = APIClient()
        cliente.force_authenticate(user=self.autor)
        respuesta = cliente.patch(
            reverse('posts_api_update', args=[self.post.id]), {'frontera_cruzada': self.caps[0].id}, format='multipart',
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(self.post, Post.objects.visible_for(lector))
        self.assertNotIn(self.comentario, Comment.objects.visible_for(lector))
        self.comentario.refresh_from_db()
        self.assertEqual(self.comentario.frontera_cruzada, self.caps[2])


class HashtagsDeComentariosTests(TestCase):
    def test_un_comentario_con_frontera_propia_no_cuelga_hashtags_del_post(self):
        obra, eps = crear_obra('serie-hashtags-comentario', 2)
        autor = User.objects.create_user('autor_hashtags_comentario', password='x')
        post = Post.objects.create(
            author=autor, obra=obra, text='post',
            referencia_narrativa=eps[0], frontera_spoiler=eps[0], frontera_origen=EXPLICITO,
        )
        Comment.objects.create(
            user=autor, post=post, text='más allá #spoilerpropio',
            referencia_narrativa=eps[0], frontera_spoiler=eps[1], frontera_origen=EXPLICITO,
        )

        self.assertFalse(post.post_hashtags.filter(hashtag__name='spoilerpropio').exists())