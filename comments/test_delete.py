from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from posts.models import Post
from .models import Comment


class DeleteCommentViewTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('del_autor', password='x')
        self.otro = User.objects.create_user('del_otro', password='x')

        self.obra = Obra.objects.create(titulo='Serie Delete', slug='serie-delete')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='post base',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        self.comentario = Comment.objects.create(
            user=self.autor, post=self.post, text='comentario a borrar',
            referencia_narrativa=self.e1,
        )

    def test_requiere_autenticacion(self):
        response = self.client.post(reverse('delete_comment', args=[self.comentario.id]))
        self.assertEqual(response.status_code, 302)

    def test_autor_puede_borrar_su_comentario(self):
        self.client.force_login(self.autor)
        response = self.client.post(reverse('delete_comment', args=[self.comentario.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Comment.objects.filter(id=self.comentario.id).exists())

    def test_otro_usuario_no_puede_borrar(self):
        self.client.force_login(self.otro)
        response = self.client.post(reverse('delete_comment', args=[self.comentario.id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(id=self.comentario.id).exists())

    def test_get_no_borra(self):
        self.client.force_login(self.autor)
        response = self.client.get(reverse('delete_comment', args=[self.comentario.id]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Comment.objects.filter(id=self.comentario.id).exists())