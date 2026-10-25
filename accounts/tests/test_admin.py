from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

NUEVA = 'Nueva-clave-segura-2026'


class UsuarioAdminTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('usuario_admin_demo', password='Clave-antigua-2026')
        self.client.force_login(User.objects.create_superuser('admin_cuentas', 'admin@example.com', 'x'))

    def test_la_ficha_del_usuario_enlaza_al_cambio_de_contrasena(self):
        response = self.client.get(reverse('admin:auth_user_change', args=[self.usuario.pk]))
        self.assertContains(response, 'href="../password/"')

    def test_el_admin_cambia_la_contrasena(self):
        url = reverse('admin:auth_user_password_change', args=[self.usuario.pk])
        response = self.client.post(url, {'password1': NUEVA, 'password2': NUEVA})
        self.assertEqual(response.status_code, 302)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(NUEVA))