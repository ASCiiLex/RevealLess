from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class InboxViewTests(TestCase):
    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('inbox'))
        self.assertEqual(response.status_code, 302)

    def test_usuario_autenticado_ve_la_bandeja(self):
        self.client.force_login(User.objects.create_user('inbox_view_user', password='x'))
        response = self.client.get(reverse('inbox'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'messages/inbox_react.html')


class ChatViewTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('chat_view_user', password='x')
        self.otro = User.objects.create_user('chat_view_otro', password='x')

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('chat', args=[self.otro.username]))
        self.assertEqual(response.status_code, 302)

    def test_usuario_autenticado_ve_el_chat(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('chat', args=[self.otro.username]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'messages/chat_react.html')

    def test_chatear_consigo_mismo_redirige_a_la_bandeja(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('chat', args=[self.usuario.username]))
        self.assertRedirects(response, reverse('inbox'), fetch_redirect_response=False)

    def test_devuelve_404_si_el_otro_usuario_no_existe(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('chat', args=['no_existe']))
        self.assertEqual(response.status_code, 404)