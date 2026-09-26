from django.contrib.auth.models import User, AnonymousUser
from django.test import TestCase

from narrative.services import actualizar_progreso
from ..models import Post
from .utils import crear_obra, crear_post


class VisibilidadPostTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user('autor', password='x')
        self.lector_avanzado = User.objects.create_user('avanzado', password='x')
        self.lector_atrasado = User.objects.create_user('atrasado', password='x')

        obra, (e1, e2, e3) = crear_obra('serie', 3)
        actualizar_progreso(self.autor, obra, e2)
        actualizar_progreso(self.lector_avanzado, obra, e3)
        actualizar_progreso(self.lector_atrasado, obra, e1)

        self.post = crear_post(self.autor, obra, e1, frontera=e3, text='spoiler gordo')

    def test_lector_avanzado_ve_el_post(self):
        self.assertIn(self.post, Post.objects.visible_for(self.lector_avanzado))

    def test_lector_atrasado_no_ve_el_post(self):
        self.assertNotIn(self.post, Post.objects.visible_for(self.lector_atrasado))

    def test_autor_ve_su_propio_post_aunque_no_haya_llegado(self):
        self.assertIn(self.post, Post.objects.visible_for(self.autor))

    def test_usuario_anonimo_no_ve_nada(self):
        self.assertFalse(Post.objects.visible_for(AnonymousUser()).exists())