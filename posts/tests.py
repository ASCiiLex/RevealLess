from django.contrib.auth.models import User, AnonymousUser
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.test import TestCase

from narrative.models import Obra, UnidadNarrativa, ProgresoUsuario, ClasificacionNarrativa
from narrative.services import actualizar_progreso
from likes.models import PostReaction
from comments.models import Comment, CommentReaction
from .models import Post


class ClasificacionNarrativaEnPostTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('autor', password='x')
        self.obra = Obra.objects.create(titulo='Serie', slug='serie')
        self.otra_obra = Obra.objects.create(titulo='Otra', slug='otra')
        self.e1 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E1', orden_local=1,
        )
        self.e2 = UnidadNarrativa.objects.create(
            obra=self.obra, tipo='episodio', nombre='E2', orden_local=2,
        )
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()
        self.unidad_otra_obra = UnidadNarrativa.objects.create(
            obra=self.otra_obra, tipo='episodio', nombre='X1', orden_local=1,
        )

    def _post(self, **kwargs):
        defaults = dict(
            author=self.autor, obra=self.obra, text='hola',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )
        defaults.update(kwargs)
        return Post(**defaults)

    def test_frontera_orden_se_calcula_al_guardar(self):
        post = self._post(frontera_spoiler=self.e2)
        post.save()
        self.assertEqual(post.frontera_orden, self.e2.orden_fin)

    def test_heredado_post_no_valido_en_post(self):
        post = self._post(frontera_origen=ClasificacionNarrativa.ORIGEN_HEREDADO_POST)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                post.save()

    def test_frontera_spoiler_obligatoria_en_post(self):
        post = self._post(frontera_spoiler=None)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                post.save()

    def test_clean_rechaza_referencia_de_otra_obra(self):
        post = self._post(referencia_narrativa=self.unidad_otra_obra)
        with self.assertRaises(ValidationError):
            post.clean()

    def test_clean_rechaza_frontera_de_otra_obra(self):
        post = self._post(frontera_spoiler=self.unidad_otra_obra)
        with self.assertRaises(ValidationError):
            post.clean()

    def test_frontera_fallback_queda_congelada_ante_avance_posterior(self):
        actualizar_progreso(self.autor, self.obra, self.e1)
        progreso = ProgresoUsuario.objects.get(usuario=self.autor, obra=self.obra)

        post = self._post(
            frontera_spoiler=progreso.unidad_actual,
            frontera_origen=ClasificacionNarrativa.ORIGEN_FALLBACK,
        )
        post.save()
        frontera_original = post.frontera_orden

        actualizar_progreso(self.autor, self.obra, self.e2)

        post.refresh_from_db()
        self.assertEqual(post.frontera_orden, frontera_original)


class VisibilidadPostTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('autor', password='x')
        self.lector_avanzado = User.objects.create_user('avanzado', password='x')
        self.lector_atrasado = User.objects.create_user('atrasado', password='x')

        self.obra = Obra.objects.create(titulo='Serie', slug='serie')
        self.e1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E1', orden_local=1)
        self.e2 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E2', orden_local=2)
        self.e3 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E3', orden_local=3)
        self.obra.recalcular_orden()
        for u in (self.e1, self.e2, self.e3):
            u.refresh_from_db()

        actualizar_progreso(self.autor, self.obra, self.e2)
        actualizar_progreso(self.lector_avanzado, self.obra, self.e3)
        actualizar_progreso(self.lector_atrasado, self.obra, self.e1)

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='spoiler gordo',
            referencia_narrativa=self.e1, frontera_spoiler=self.e3,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_lector_avanzado_ve_el_post(self):
        self.assertIn(self.post, Post.objects.visible_for(self.lector_avanzado))

    def test_lector_atrasado_no_ve_el_post(self):
        self.assertNotIn(self.post, Post.objects.visible_for(self.lector_atrasado))

    def test_autor_ve_su_propio_post_aunque_no_haya_llegado(self):
        self.assertIn(self.post, Post.objects.visible_for(self.autor))

    def test_usuario_anonimo_no_ve_nada(self):
        visibles = Post.objects.visible_for(AnonymousUser())
        self.assertFalse(visibles.exists())


class FeedStatsQuerySetTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('autor_stats', password='x')
        self.otro = User.objects.create_user('otro_stats', password='x')
        self.tercero = User.objects.create_user('tercero_stats', password='x')

        self.obra = Obra.objects.create(titulo='Serie Stats', slug='serie-stats')
        self.e1 = UnidadNarrativa.objects.create(obra=self.obra, tipo='episodio', nombre='E1', orden_local=1)
        self.obra.recalcular_orden()
        self.e1.refresh_from_db()

        self.post = Post.objects.create(
            author=self.autor, obra=self.obra, text='post con stats',
            referencia_narrativa=self.e1, frontera_spoiler=self.e1,
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
        )

    def test_post_sin_interacciones_tiene_conteos_a_cero(self):
        post = Post.objects.with_feed_stats().get(pk=self.post.pk)
        self.assertEqual(post.likes_count, 0)
        self.assertEqual(post.comments_count, 0)

    def test_conteos_correctos_con_likes_y_comentarios(self):
        PostReaction.objects.create(user=self.otro, post=self.post, reaction='like')
        PostReaction.objects.create(user=self.tercero, post=self.post, reaction='love')

        Comment.objects.create(
            user=self.otro, post=self.post, text='comentario 1',
            referencia_narrativa=self.e1,
        )
        Comment.objects.create(
            user=self.tercero, post=self.post, text='comentario 2',
            referencia_narrativa=self.e1,
        )
        Comment.objects.create(
            user=self.autor, post=self.post, text='comentario 3',
            referencia_narrativa=self.e1,
        )

        post = Post.objects.with_feed_stats().get(pk=self.post.pk)
        self.assertEqual(post.likes_count, 2)
        self.assertEqual(post.comments_count, 3)

    def test_conteos_no_se_inflan_con_reacciones_a_comentarios(self):
        # Riesgo conocido: Count combinados sobre relaciones distintas puede
        # generar joins cartesianos. Este test vigila que reacciones a
        # comentarios (relación distinta) no contaminen los conteos del post.
        comment = Comment.objects.create(
            user=self.otro, post=self.post, text='comentario',
            referencia_narrativa=self.e1,
        )
        CommentReaction.objects.create(user=self.tercero, comment=comment, reaction='like')
        PostReaction.objects.create(user=self.otro, post=self.post, reaction='like')

        post = Post.objects.with_feed_stats().get(pk=self.post.pk)
        self.assertEqual(post.likes_count, 1)
        self.assertEqual(post.comments_count, 1)

    def test_visible_for_y_with_feed_stats_se_combinan_sin_perder_anotaciones(self):
        PostReaction.objects.create(user=self.otro, post=self.post, reaction='like')
        Comment.objects.create(
            user=self.otro, post=self.post, text='comentario',
            referencia_narrativa=self.e1,
        )

        post = Post.objects.visible_for(self.autor).with_feed_stats().get(pk=self.post.pk)
        self.assertEqual(post.likes_count, 1)
        self.assertEqual(post.comments_count, 1)