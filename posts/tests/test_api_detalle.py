from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from comments.models import Comment, CommentReaction
from likes.models import PostReaction
from narrative.services import actualizar_progreso
from .utils import crear_obra, crear_post


class PostDetailAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user('detalle_autor', password='x')
        self.lector = User.objects.create_user('detalle_lector', password='x')

        self.obra, (self.e1, self.e2) = crear_obra('serie-detalle-post', 2)
        # El lector alcanza e1; un anónimo (progreso 0) nunca llega a frontera_orden > 0.
        actualizar_progreso(self.lector, self.obra, self.e1)
        self.post = crear_post(self.autor, self.obra, self.e1, text='post de prueba')

    def _get(self, user=None, post=None, **params):
        if user:
            self.client.force_authenticate(user=user)
        return self.client.get(reverse('posts_api_detail', args=[(post or self.post).id]), params)

    def _comentar(self, user, text, parent=None):
        return Comment.objects.create(
            user=user, post=self.post, parent=parent, text=text, referencia_narrativa=self.e1,
        )

    def test_visible_para_usuario_con_progreso_suficiente(self):
        self.assertEqual(self._get(self.lector).status_code, 200)

    def test_anonimo_sin_progreso_recibe_404(self):
        self.assertEqual(self._get().status_code, 404)

    def test_autor_ve_su_propio_post_sin_progreso(self):
        self.assertEqual(self._get(self.autor).status_code, 200)

    def test_devuelve_404_si_no_visible_para_el_usuario(self):
        bloqueado = crear_post(self.autor, self.obra, self.e1, frontera=self.e2, text='con spoiler')
        self.assertEqual(self._get(self.lector, post=bloqueado).status_code, 404)

    def test_incluye_datos_del_post(self):
        self.assertEqual(self._get(self.lector).data['post']['id'], self.post.id)

    def test_incluye_comentarios_de_nivel_superior(self):
        self._comentar(self.lector, 'un comentario')
        self.assertEqual(len(self._get(self.lector).data['comments']), 1)

    def test_incluye_replies_anidadas(self):
        padre = self._comentar(self.lector, 'padre')
        self._comentar(self.autor, 'reply', parent=padre)
        self.assertEqual(len(self._get(self.lector).data['comments'][0]['replies']), 1)

    def test_incluye_user_reaction_del_post(self):
        PostReaction.objects.create(user=self.lector, post=self.post, reaction='love')
        self.assertEqual(self._get(self.lector).data['post_reaction'], 'love')

    def test_post_reaction_es_none_sin_reaccion(self):
        self.assertIsNone(self._get(self.lector).data['post_reaction'])

    def test_ordena_por_popular(self):
        self._comentar(self.lector, 'poco popular')
        popular = self._comentar(self.autor, 'muy popular')
        CommentReaction.objects.create(user=self.autor, comment=popular, reaction='like')
        CommentReaction.objects.create(user=self.lector, comment=popular, reaction='love')

        response = self._get(self.lector, sort='popular')
        self.assertEqual(response.data['comments'][0]['id'], popular.id)