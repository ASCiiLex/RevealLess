from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class NavegacionBaseHtmlTests(TestCase):
    """base.html y profile.html son plantillas clásicas todavía en uso;
    confirma que sus enlaces apuntan a las vistas React, no a las rutas
    de inbox/chat/notifications ya borradas."""

    def setUp(self):
        self.usuario = User.objects.create_user('nav_user', password='x')
        self.otro = User.objects.create_user('nav_otro', password='x')
        self.client.force_login(self.usuario)

    def test_header_enlaza_notificaciones_react(self):
        response = self.client.get(reverse('profile', args=[self.usuario.username]))
        self.assertContains(response, 'href="/notificaciones/react/"')

    def test_header_enlaza_mensajes_react(self):
        response = self.client.get(reverse('profile', args=[self.usuario.username]))
        self.assertContains(response, 'href="/mensajes/react/"')

    def test_perfil_ajeno_enlaza_chat_react(self):
        response = self.client.get(reverse('profile', args=[self.otro.username]))
        self.assertContains(response, f'href="/mensajes/chat-react/{self.otro.username}/"')