import re

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from follows.models import Follow


class BotonSeguirEnPerfilTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('perfil_seguidor', password='x')
        self.otro = User.objects.create_user('perfil_seguido', password='x')
        self.client.force_login(self.usuario)

    def _texto_del_boton(self, response):
        contenido = response.content.decode()
        match = re.search(
            r'id="follow-toggle-btn".*?>\s*(.*?)\s*</button>', contenido, re.DOTALL
        )
        self.assertIsNotNone(match, 'No se encontró el botón follow-toggle-btn en la respuesta.')
        return match.group(1).strip()

    def test_muestra_boton_seguir_si_no_sigue(self):
        response = self.client.get(reverse('profile', args=[self.otro.username]))
        self.assertContains(response, 'data-following="false"')
        self.assertEqual(self._texto_del_boton(response), 'Seguir')

    def test_muestra_boton_dejar_de_seguir_si_ya_sigue(self):
        Follow.objects.create(follower=self.usuario, followed=self.otro)
        response = self.client.get(reverse('profile', args=[self.otro.username]))
        self.assertContains(response, 'data-following="true"')
        self.assertEqual(self._texto_del_boton(response), 'Dejar de seguir')

    def test_boton_apunta_a_la_api_no_a_rutas_borradas(self):
        response = self.client.get(reverse('profile', args=[self.otro.username]))
        self.assertContains(response, "/follows/api/")
        self.assertNotContains(response, 'action="/follows/follow/')
        self.assertNotContains(response, 'action="/follows/unfollow/')