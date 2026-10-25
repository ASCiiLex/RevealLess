from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

ACTUAL = 'Clave-actual-2026'
NUEVA = 'Nueva-clave-segura-2026'


class CambioPasswordAPIViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.usuario = User.objects.create_user('cambio_password', password=ACTUAL)
        self.client = APIClient()
        self.client.force_login(self.usuario)

    def _cambiar(self, actual=ACTUAL, password=NUEVA, password2=NUEVA, cliente=None):
        return (cliente or self.client).post(reverse('accounts_api_password'), {
            'password_actual': actual, 'password': password, 'password2': password2,
        })

    def _password_es(self, valor):
        self.usuario.refresh_from_db()
        return self.usuario.check_password(valor)

    def test_cambia_la_contrasena(self):
        self.assertEqual(self._cambiar().status_code, 204)
        self.assertTrue(self._password_es(NUEVA))

    def test_mantiene_la_sesion_actual(self):
        self._cambiar()
        self.assertEqual(self.client.get(reverse('api_me')).status_code, 200)

    def test_cierra_las_sesiones_de_otros_dispositivos(self):
        otro_dispositivo = APIClient()
        otro_dispositivo.force_login(self.usuario)
        self._cambiar()
        self.assertEqual(otro_dispositivo.get(reverse('api_me')).status_code, 403)

    def test_rechaza_la_contrasena_actual_incorrecta(self):
        response = self._cambiar(actual='incorrecta')
        self.assertEqual(response.status_code, 400)
        self.assertIn('password_actual', response.data)
        self.assertTrue(self._password_es(ACTUAL))

    def test_rechaza_contrasenas_distintas(self):
        response = self._cambiar(password2='Otra-clave-distinta-2026')
        self.assertEqual(response.status_code, 400)
        self.assertIn('password2', response.data)
        self.assertTrue(self._password_es(ACTUAL))

    def test_rechaza_contrasena_debil(self):
        response = self._cambiar(password='12345678', password2='12345678')
        self.assertEqual(response.status_code, 400)
        self.assertIn('password', response.data)
        self.assertTrue(self._password_es(ACTUAL))

    def test_exige_sesion(self):
        self.assertEqual(self._cambiar(cliente=APIClient()).status_code, 403)

    def test_exige_token_csrf(self):
        cliente = APIClient(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        self.assertEqual(self._cambiar(cliente=cliente).status_code, 403)
        self.assertTrue(self._password_es(ACTUAL))

    def test_limita_los_intentos_por_minuto(self):
        for _ in range(5):
            self.assertEqual(self._cambiar(actual='incorrecta').status_code, 400)
        self.assertEqual(self._cambiar().status_code, 403)
        self.assertTrue(self._password_es(ACTUAL))