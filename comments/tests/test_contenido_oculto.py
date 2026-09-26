from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from posts.models import Post
from ..models import Comment, CommentReaction


class ContenidoOcultoComentariosTests(TestCase):
    """Sin progreso suficiente no se puede comentar, responder ni reaccionar."""

    def setUp(self):
        autor = User.objects.create_user('oculto_autor', password='x')
        lector = User.objects.create_user('oculto_lector', password='x')

        obra = Obra.objects.create(titulo='Serie Oculta', slug='serie-oculta')
        e1 = UnidadNarrativa.objects.create(obra=obra, tipo='episodio', nombre='E1', orden_local=1)
        e3 = UnidadNarrativa.objects.create(obra=obra, tipo='episodio', nombre='E3', orden_local=3)
        obra.recalcular_orden()
        e1.refresh_from_db()
        e3.refresh_from_db()
        actualizar_progreso(lector, obra, e1)

        def crear_post(text, frontera):
            return Post.objects.create(
                author=autor, obra=obra, text=text,
                referencia_narrativa=e1, frontera_spoiler=frontera,
                frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
            )

        self.post_visible = crear_post('post visible', e1)
        self.post_oculto = crear_post('post oculto', e3)
        self.comentario_visible = Comment.objects.create(
            user=autor, post=self.post_visible, text='comentario visible',
            referencia_narrativa=e1,
        )
        self.comentario_oculto = Comment.objects.create(
            user=autor, post=self.post_visible, text='comentario oculto',
            referencia_narrativa=e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
            frontera_spoiler=e3,
        )
        self.client.force_login(lector)

    def _reaccionar(self, comentario):
        return self.client.post(
            reverse('toggle_reaction_comment', args=[comentario.id]), {'reaction': 'me_gusta'},
        )

    def test_no_se_puede_comentar_en_un_post_oculto(self):
        response = self.client.post(reverse('add_comment'), {
            'post_id': self.post_oculto.id, 'text': 'intento colarme',
        })
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Comment.objects.filter(text='intento colarme').exists())

    def test_no_se_puede_responder_a_un_comentario_oculto(self):
        response = self.client.post(reverse('add_comment'), {
            'post_id': self.post_visible.id, 'text': 'respuesta a oculto',
            'parent_id': self.comentario_oculto.id,
        })
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Comment.objects.filter(text='respuesta a oculto').exists())

    def test_no_se_puede_reaccionar_a_un_comentario_oculto(self):
        self.assertEqual(self._reaccionar(self.comentario_oculto).status_code, 404)
        self.assertFalse(CommentReaction.objects.filter(comment=self.comentario_oculto).exists())

    def test_no_se_pueden_listar_reacciones_de_un_comentario_oculto(self):
        response = self.client.get(reverse('comment_reactions_list', args=[self.comentario_oculto.id]))
        self.assertEqual(response.status_code, 404)

    def test_se_puede_reaccionar_a_un_comentario_visible(self):
        self.assertEqual(self._reaccionar(self.comentario_visible).status_code, 200)
        self.assertTrue(CommentReaction.objects.filter(comment=self.comentario_visible).exists())