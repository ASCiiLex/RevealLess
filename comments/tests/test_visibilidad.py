from django.contrib.auth.models import User, AnonymousUser
from django.test import TestCase

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from posts.models import Post
from ..models import Comment


class VisibilidadCommentTests(TestCase):
    def setUp(self):
        self.autor_post = User.objects.create_user('autor_post', password='x')
        self.lector_avanzado = User.objects.create_user('avanzado', password='x')
        self.lector_atrasado = User.objects.create_user('atrasado', password='x')

        self.obra = Obra.objects.create(titulo='Serie', slug='serie')
        self.e1, self.e2, self.e3 = (
            UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre=f'E{n}', orden_local=n)
            for n in (1, 2, 3)
        )
        self.obra.recalcular_orden()
        for u in (self.e1, self.e2, self.e3):
            u.refresh_from_db()

        actualizar_progreso(self.lector_avanzado, self.obra, self.e3)
        actualizar_progreso(self.lector_atrasado, self.obra, self.e1)

        self.post = Post.objects.create(
            author=self.autor_post, obra=self.obra, text='post',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        self.comentario_restrictivo = Comment.objects.create(
            user=self.autor_post, post=self.post, text='comentario spoiler',
            referencia_narrativa=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
            frontera_spoiler=self.e3,
        )

    def test_comentario_no_visible_si_no_alcanza_su_propia_frontera(self):
        self.assertNotIn(self.comentario_restrictivo, Comment.objects.visible_for(self.lector_atrasado))

    def test_comentario_visible_si_alcanza_su_propia_frontera(self):
        self.assertIn(self.comentario_restrictivo, Comment.objects.visible_for(self.lector_avanzado))

    def test_comentario_nunca_visible_si_su_post_no_lo_es(self):
        post_bloqueado = Post.objects.create(
            author=self.autor_post, obra=self.obra, text='post bloqueado',
            referencia_narrativa=self.e1, frontera_spoiler=self.e3,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        comentario = Comment.objects.create(
            user=self.autor_post, post=post_bloqueado, text='inofensivo',
            referencia_narrativa=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
            frontera_spoiler=self.e1,
        )
        self.assertNotIn(comentario, Comment.objects.visible_for(self.lector_atrasado))

    def test_usuario_anonimo_no_ve_comentarios(self):
        self.assertFalse(Comment.objects.visible_for(AnonymousUser()).exists())