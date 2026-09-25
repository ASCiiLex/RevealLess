from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class VistaReactGuardadosTests(TestCase):
    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('saved_posts_react'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/cuentas/login/', response.url)

    def test_usuario_autenticado_ve_la_pantalla(self):
        self.client.force_login(User.objects.create_user('guardados_react', password='x'))
        response = self.client.get(reverse('saved_posts_react'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'saved_posts/saved_posts_react.html')