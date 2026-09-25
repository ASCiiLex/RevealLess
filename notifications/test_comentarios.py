from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from comments.models import Comment
from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from posts.models import Post
from .models import Notification


class NotificacionesComentariosTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('notifc_autor', password='x')
        self.lector = User.objects.create_user('notifc_lector', password='x')

        self.obra = Obra.objects.create(titulo='Serie Notif Comentarios', slug='serie-notif-comentarios')
        self.e1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E1', orden_local=1)
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        actualizar_progreso(self.lector, self.obra, self.e1)

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='post base',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        self.client.force_login(self.lector)

    def _comentario_del_autor(self):
        comentario = Comment.objects.create(
            user=self.autor, post=self.post, text='comentario del autor',
            referencia_narrativa=self.e1,
        )
        # Evita que el id del comentario coincida con el del post.
        while comentario.id == self.post.id:
            comentario = Comment.objects.create(
                user=self.autor, post=self.post, text='comentario del autor',
                referencia_narrativa=self.e1,
            )
        return comentario

    def test_comentar_genera_una_sola_notificacion(self):
        self.client.post(reverse('add_comment'), {'post_id': self.post.id, 'text': 'hola'})
        self.assertEqual(Notification.objects.filter(user=self.autor).count(), 1)

    def test_responder_genera_una_sola_notificacion(self):
        padre = self._comentario_del_autor()
        self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'respuesta', 'parent_id': padre.id,
        })
        self.assertEqual(Notification.objects.filter(user=self.autor).count(), 1)

    def test_reaccionar_a_un_comentario_genera_una_sola_notificacion(self):
        comentario = self._comentario_del_autor()
        self.client.post(
            reverse('toggle_reaction_comment', args=[comentario.id]),
            {'reaction': 'me_gusta'},
        )
        self.assertEqual(Notification.objects.filter(user=self.autor).count(), 1)

    def test_enlace_de_una_respuesta_apunta_al_post_del_comentario(self):
        padre = self._comentario_del_autor()
        self.client.post(reverse('add_comment'), {
            'post_id': self.post.id, 'text': 'respuesta', 'parent_id': padre.id,
        })
        notificacion = Notification.objects.get(user=self.autor)
        self.assertEqual(notificacion.url, f'/posts/{self.post.id}/')

    def test_enlace_de_una_reaccion_a_comentario_apunta_al_post_del_comentario(self):
        comentario = self._comentario_del_autor()
        self.client.post(
            reverse('toggle_reaction_comment', args=[comentario.id]),
            {'reaction': 'me_gusta'},
        )
        notificacion = Notification.objects.get(user=self.autor)
        self.assertEqual(notificacion.url, f'/posts/{self.post.id}/')