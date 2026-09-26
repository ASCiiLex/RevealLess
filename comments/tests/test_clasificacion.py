from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from narrative.models import Obra, UnidadNarrativa, ClasificacionNarrativa
from posts.models import Post
from ..models import Comment


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

    def _comentario(self, **kwargs):
        return Comment(
            user=self.autor_comentario, post=self.post, text='x',
            referencia_narrativa=self.e1, **kwargs,
        )

    def test_comentario_por_defecto_hereda_del_post(self):
        comentario = self._comentario()
        comentario.save()
        self.assertEqual(comentario.frontera_origen, ClasificacionNarrativa.ORIGEN_HEREDADO_POST)
        self.assertIsNone(comentario.frontera_spoiler)
        self.assertIsNone(comentario.frontera_orden)
        self.assertEqual(comentario.frontera_efectiva_orden, self.post.frontera_orden)

    def test_heredado_post_exige_frontera_spoiler_nula(self):
        comentario = self._comentario(
            frontera_origen=ClasificacionNarrativa.ORIGEN_HEREDADO_POST,
            frontera_spoiler=self.e1,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                comentario.save()

    def test_clasificacion_propia_exige_frontera_spoiler(self):
        comentario = self._comentario(
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
            frontera_spoiler=None,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                comentario.save()

    def test_clasificacion_propia_calcula_su_propia_frontera(self):
        comentario = self._comentario(
            frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
            frontera_spoiler=self.e1,
        )
        comentario.save()
        self.assertEqual(comentario.frontera_orden, self.e1.orden_fin)
        self.assertEqual(comentario.frontera_efectiva_orden, self.e1.orden_fin)