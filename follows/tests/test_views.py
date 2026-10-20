from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class VistasReactSeguidoresTests(TestCase):
    def setUp(self):
        User.objects.create_user('lista_react', password='x')

    def test_seguidores_responde_200_sin_login(self):
        response = self.client.get(reverse('followers', args=['lista_react']))
        self.assertEqual(response.status_code, 200)

    def test_seguidores_devuelve_404_si_el_usuario_no_existe(self):
        response = self.client.get(reverse('followers', args=['no_existe']))
        self.assertEqual(response.status_code, 404)

    def test_siguiendo_responde_200_sin_login(self):
        response = self.client.get(reverse('following', args=['lista_react']))
        self.assertEqual(response.status_code, 200)

    def test_siguiendo_devuelve_404_si_el_usuario_no_existe(self):
        response = self.client.get(reverse('following', args=['no_existe']))
        self.assertEqual(response.status_code, 404)