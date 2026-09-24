from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class LogoutTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('logout_user', password='x')
        self.client.force_login(self.usuario)

    def test_get_no_cierra_la_sesion(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_post_cierra_la_sesion(self):
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 204)
        self.assertNotIn('_auth_user_id', self.client.session)