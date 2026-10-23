from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class LoginAPIViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.usuario = User.objects.create_user('login_test', password='ContraseñaSegura123')

    def test_login_correcto_inicia_sesion(self):
        response = self.client.post(reverse('accounts_api_login'), {
            'username': 'login_test', 'password': 'ContraseñaSegura123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'login_test')

    def test_login_incorrecto_devuelve_400(self):
        response = self.client.post(reverse('accounts_api_login'), {
            'username': 'login_test', 'password': 'incorrecta',
        })
        self.assertEqual(response.status_code, 400)

    def test_login_deja_sesion_autenticada(self):
        self.client.post(reverse('accounts_api_login'), {
            'username': 'login_test', 'password': 'ContraseñaSegura123',
        })
        response = self.client.get(reverse('api_me'))
        self.assertEqual(response.status_code, 200)


class RegisterAPIViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def _registrar(self, username):
        return self.client.post(reverse('accounts_api_register'), {
            'username': username,
            'email': 'regla@example.com',
            'password': 'ContraseñaSegura123',
            'password2': 'ContraseñaSegura123',
        })

    def test_registro_correcto_crea_usuario(self):
        response = self.client.post(reverse('accounts_api_register'), {
            'username': 'nuevo_usuario',
            'email': 'nuevo@example.com',
            'password': 'ContraseñaSegura123',
            'password2': 'ContraseñaSegura123',
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='nuevo_usuario').exists())

    def test_registro_inicia_sesion_automaticamente(self):
        self.client.post(reverse('accounts_api_register'), {
            'username': 'nuevo_usuario2',
            'email': 'nuevo2@example.com',
            'password': 'ContraseñaSegura123',
            'password2': 'ContraseñaSegura123',
        })
        response = self.client.get(reverse('api_me'))
        self.assertEqual(response.status_code, 200)

    def test_registro_rechaza_contrasenas_distintas(self):
        response = self.client.post(reverse('accounts_api_register'), {
            'username': 'usuario_x',
            'email': 'x@example.com',
            'password': 'ContraseñaSegura123',
            'password2': 'OtraDistinta456',
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username='usuario_x').exists())

    def test_registro_rechaza_contrasena_debil(self):
        response = self.client.post(reverse('accounts_api_register'), {
            'username': 'usuario_debil',
            'email': 'debil@example.com',
            'password': '123',
            'password2': '123',
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username='usuario_debil').exists())

    def test_registro_rechaza_username_duplicado(self):
        User.objects.create_user('existente', password='x')
        response = self.client.post(reverse('accounts_api_register'), {
            'username': 'existente',
            'email': 'otro@example.com',
            'password': 'ContraseñaSegura123',
            'password2': 'ContraseñaSegura123',
        })
        self.assertEqual(response.status_code, 400)

    def test_registro_rechaza_email_duplicado(self):
        User.objects.create_user('otro_user', email='duplicado@example.com', password='x')
        response = self.client.post(reverse('accounts_api_register'), {
            'username': 'usuario_nuevo3',
            'email': 'duplicado@example.com',
            'password': 'ContraseñaSegura123',
            'password2': 'ContraseñaSegura123',
        })
        self.assertEqual(response.status_code, 400)

    def test_registro_sin_imagen_es_valido(self):
        response = self.client.post(reverse('accounts_api_register'), {
            'username': 'sin_imagen',
            'email': 'sinimagen@example.com',
            'password': 'ContraseñaSegura123',
            'password2': 'ContraseñaSegura123',
        })
        self.assertEqual(response.status_code, 201)

    def test_registro_rechaza_username_con_espacios_o_acentos(self):
        response = self._registrar('josé garcía')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email='regla@example.com').exists())

    def test_registro_rechaza_username_con_signos(self):
        # El punto y la barra rompen la ruta del chat y la del perfil.
        response = self._registrar('ana.garcia/1')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email='regla@example.com').exists())

    def test_registro_rechaza_username_de_mas_de_30(self):
        response = self._registrar('a' * 31)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email='regla@example.com').exists())

    def test_registro_admite_username_de_30(self):
        response = self._registrar('a' * 30)
        self.assertEqual(response.status_code, 201)