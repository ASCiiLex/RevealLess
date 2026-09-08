from django.contrib.auth.models import User, AnonymousUser
from django.db import IntegrityError, transaction
from django.test import TestCase

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from posts.models import Post
from .models import Comment


class ClasificacionNarrativaEnCommentTests(TestCase):
    def setUp(self):
        self.autor_post = User.objects.create_user('autor_post', password='x')
        self.autor_comentario = User.objects.create_user('autor_comentario', password='x')
        self.obra = Obra.objects.create(titulo='Serie', slug='serie')
        self.e1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E1', orden_local=1)
        self.e2 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E2', orden_local=2)
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()

        self.post = Post.objects.create(
            author=self.autor_post, obra=self.obra, text='post',
            referencia_narrativa=self.e1, frontera_spoiler=self.e2,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_comentario_por_defecto_hereda_del_post(self):
        comentario = Comment.objects.create(
            user=self.autor_comentario, post=self.post,
            text='comentario', referencia_narrativa=self.e1,
        )
        self.assertEqual(comentario.frontera_origen, ClasificacionNarrativa.ORIGEN_HEREDADO_POST)
        self.assertIsNone(comentario.frontera_spoiler)
        self.assertIsNone(comentario.frontera_orden)
        self.assertEqual(comentario.frontera_efectiva_orden, self.post.frontera_orden)

    def test_heredado_post_exige_frontera_spoiler_nula(self):
        comentario = Comment(
            user=self.autor_comentario, post=self.post, text='x',
            referencia_narrativa=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_HEREDADO_POST,
            frontera_spoiler=self.e1,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                comentario.save()

    def test_clasificacion_propia_exige_frontera_spoiler(self):
        comentario = Comment(
            user=self.autor_comentario, post=self.post, text='x',
            referencia_narrativa=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
            frontera_spoiler=None,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                comentario.save()

    def test_clasificacion_propia_calcula_su_propia_frontera(self):
        comentario = Comment.objects.create(
            user=self.autor_comentario, post=self.post, text='x',
            referencia_narrativa=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
            frontera_spoiler=self.e1,
        )
        self.assertEqual(comentario.frontera_orden, self.e1.orden_fin)
        self.assertEqual(comentario.frontera_efectiva_orden, self.e1.orden_fin)


class VisibilidadCommentTests(TestCase):
    def setUp(self):
        self.autor_post = User.objects.create_user('autor_post', password='x')
        self.lector_avanzado = User.objects.create_user('avanzado', password='x')
        self.lector_atrasado = User.objects.create_user('atrasado', password='x')

        self.obra = Obra.objects.create(titulo='Serie', slug='serie')
        self.e1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E1', orden_local=1)
        self.e2 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E2', orden_local=2)
        self.e3 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E3', orden_local=3)
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
        visibles = Comment.objects.visible_for(AnonymousUser())
        self.assertFalse(visibles.exists())