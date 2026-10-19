from django.contrib.auth.models import User
from django.test import TestCase

from narrative.models import ClasificacionNarrativa
from narrative.services import actualizar_progreso
from posts.tests.utils import crear_obra, crear_post
from ..models import Comment
from ..views.fronteras import ajustar_frontera

HEREDADO = ClasificacionNarrativa.ORIGEN_HEREDADO_POST
EXPLICITO = ClasificacionNarrativa.ORIGEN_EXPLICITO


class FronteraMinimaComentarioTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('autor_comentario_minimo', password='x')
        self.lector = User.objects.create_user('lector_comentario_minimo', password='x')
        self.obra, self.eps = crear_obra('comentario-minimo', 3)
        self.post = crear_post(self.autor, self.obra, self.eps[0])
        actualizar_progreso(self.lector, self.obra, self.eps[0])

    def _comentario(self, referencia, frontera=None):
        comment = Comment(user=self.autor, post=self.post, text='c', referencia_narrativa=referencia)
        if frontera:
            comment.frontera_spoiler = frontera
            comment.frontera_origen = EXPLICITO
        ajustar_frontera(comment)
        comment.save()
        return comment

    def test_heredado_dentro_de_la_frontera_del_post_sigue_heredado(self):
        comment = self._comentario(self.eps[0])
        self.assertEqual(comment.frontera_origen, HEREDADO)
        self.assertIsNone(comment.frontera_spoiler)
        self.assertIn(comment, Comment.objects.visible_for(self.lector))

    def test_heredado_con_referencia_posterior_pasa_a_frontera_propia(self):
        comment = self._comentario(self.eps[2])
        self.assertEqual(comment.frontera_origen, EXPLICITO)
        self.assertEqual(comment.frontera_spoiler, self.eps[2])
        self.assertNotIn(comment, Comment.objects.visible_for(self.lector))

    def test_frontera_propia_anterior_a_la_referencia_se_eleva(self):
        comment = self._comentario(self.eps[1], frontera=self.eps[0])
        self.assertEqual(comment.frontera_spoiler, self.eps[1])

    def test_frontera_propia_posterior_se_respeta(self):
        comment = self._comentario(self.eps[0], frontera=self.eps[2])
        self.assertEqual(comment.frontera_spoiler, self.eps[2])