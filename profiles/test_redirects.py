from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class VistasClasicasRedirigenAReactTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('redir_profile_user', password='x')

    def test_profile_view_redirige_a_react(self):
        response = self.client.get(reverse('profile', args=[self.usuario.username]))
        self.assertRedirects(
            response, f'/perfil/{self.usuario.username}/react/', fetch_redirect_response=False
        )

    def test_followers_view_redirige_a_react(self):
        response = self.client.get(reverse('followers', args=[self.usuario.username]))
        self.assertRedirects(
            response, f'/follows/seguidores-react/{self.usuario.username}/', fetch_redirect_response=False
        )

    def test_following_view_redirige_a_react(self):
        response = self.client.get(reverse('following', args=[self.usuario.username]))
        self.assertRedirects(
            response, f'/follows/siguiendo-react/{self.usuario.username}/', fetch_redirect_response=False
        )