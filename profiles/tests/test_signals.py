from django.contrib.auth.models import User
from django.test import TestCase

from ..models import Profile


class SenalPerfilTests(TestCase):
    def test_crear_usuario_crea_su_perfil(self):
        usuario = User.objects.create_user('senal_nuevo', password='x')
        self.assertTrue(Profile.objects.filter(user=usuario).exists())

    def test_guardar_usuario_no_duplica_el_perfil(self):
        usuario = User.objects.create_user('senal_dup', password='x')
        usuario.first_name = 'Cambio'
        usuario.save()
        self.assertEqual(Profile.objects.filter(user=usuario).count(), 1)

    def test_guardar_usuario_sin_perfil_lo_recrea(self):
        usuario = User.objects.create_user('senal_sin_perfil', password='x')
        Profile.objects.filter(user=usuario).delete()

        usuario = User.objects.get(pk=usuario.pk)
        usuario.save()

        self.assertTrue(Profile.objects.filter(user=usuario).exists())

    def test_login_de_usuario_sin_perfil_no_falla(self):
        usuario = User.objects.create_user('senal_login', password='x')
        Profile.objects.filter(user=usuario).delete()

        self.assertTrue(self.client.login(username='senal_login', password='x'))
        self.assertTrue(Profile.objects.filter(user=usuario).exists())