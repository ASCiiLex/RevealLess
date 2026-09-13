from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from notifications.models import Notification
from .models import Follow


class FollowToggleAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('seguidor', password='x')
        self.otro = User.objects.create_user('seguido', password='x')

    def test_requiere_autenticacion_para_seguir(self):
        response = self.client.post(reverse('follows_api_toggle', args=['seguido']))
        self.assertEqual(response.status_code, 403)

    def test_post_crea_el_follow(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.post(reverse('follows_api_toggle', args=['seguido']))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_following'])
        self.assertTrue(
            Follow.objects.filter(follower=self.usuario, followed=self.otro).exists()
        )

    def test_post_es_idempotente(self):
        self.client.force_authenticate(user=self.usuario)
        self.client.post(reverse('follows_api_toggle', args=['seguido']))
        self.client.post(reverse('follows_api_toggle', args=['seguido']))
        self.assertEqual(
            Follow.objects.filter(follower=self.usuario, followed=self.otro).count(), 1
        )

    def test_post_dispara_notificacion_solo_una_vez(self):
        self.client.force_authenticate(user=self.usuario)
        self.client.post(reverse('follows_api_toggle', args=['seguido']))
        self.client.post(reverse('follows_api_toggle', args=['seguido']))
        self.assertEqual(
            Notification.objects.filter(user=self.otro, target_type='follow').count(), 1
        )

    def test_no_permite_seguirse_a_si_mismo(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.post(reverse('follows_api_toggle', args=['seguidor']))
        self.assertEqual(response.status_code, 400)

    def test_delete_elimina_el_follow(self):
        Follow.objects.create(follower=self.usuario, followed=self.otro)
        self.client.force_authenticate(user=self.usuario)
        response = self.client.delete(reverse('follows_api_toggle', args=['seguido']))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['is_following'])
        self.assertFalse(
            Follow.objects.filter(follower=self.usuario, followed=self.otro).exists()
        )

    def test_delete_sin_follow_previo_no_falla(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.delete(reverse('follows_api_toggle', args=['seguido']))
        self.assertEqual(response.status_code, 200)