from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Notification


class VerboNotificacionTests(TestCase):
    def setUp(self):
        self.actor = User.objects.create_user('verbo_actor', password='x')
        self.usuario = User.objects.create_user('verbo_usuario', password='x')

    def _notif(self, verb, target_type='post'):
        return Notification(actor=self.actor, user=self.usuario, verb=verb, target_type=target_type)

    def test_commented_se_traduce(self):
        self.assertEqual(self._notif('commented').verb_display, 'comentó tu publicación')

    def test_replied_se_traduce(self):
        self.assertEqual(self._notif('replied', 'comment').verb_display, 'respondió a tu comentario')

    def test_mentioned_se_traduce(self):
        self.assertEqual(
            self._notif('mentioned', 'comment').verb_display, 'te ha mencionado en un comentario'
        )

    def test_reacted_a_post_se_traduce(self):
        self.assertEqual(self._notif('reacted', 'post').verb_display, 'reaccionó a tu publicación')

    def test_reacted_a_comentario_se_traduce(self):
        self.assertEqual(self._notif('reacted', 'comment').verb_display, 'reaccionó a tu comentario')

    def test_verbo_desconocido_se_devuelve_sin_cambios(self):
        self.assertEqual(self._notif('te ha seguido', 'follow').verb_display, 'te ha seguido')

    def test_la_api_devuelve_el_verbo_traducido(self):
        Notification.objects.create(
            actor=self.actor, user=self.usuario, verb='commented', target_type='post',
        )
        client = APIClient()
        client.force_authenticate(user=self.usuario)
        response = client.get(reverse('notifications_api_list'))
        self.assertEqual(response.data['results'][0]['verb'], 'comentó tu publicación')