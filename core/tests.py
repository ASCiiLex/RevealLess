from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from messages_app.models import Message
from notifications.models import Notification


class MeAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('usuario_me', password='x')
        self.otro = User.objects.create_user('otro_me', password='x')

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('api_me'))
        self.assertEqual(response.status_code, 403)

    def test_devuelve_username(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('api_me'))
        self.assertEqual(response.data['username'], 'usuario_me')

    def test_avatar_por_defecto_sin_imagen(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('api_me'))
        self.assertEqual(response.data['avatar_url'], '/static/img/default_profile.jpg')

    def test_unread_count_suma_notificaciones_y_mensajes(self):
        Notification.objects.create(
            user=self.usuario, actor=self.otro, verb='te ha seguido', target_type='follow',
        )
        Notification.objects.create(
            user=self.usuario, actor=self.otro, verb='commented', target_type='post', target_id=1,
        )
        Message.objects.create(sender=self.otro, receiver=self.usuario, text='hola')

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('api_me'))
        self.assertEqual(response.data['unread_count'], 3)

    def test_notificacion_vista_no_cuenta(self):
        Notification.objects.create(
            user=self.usuario, actor=self.otro, verb='te ha seguido',
            target_type='follow', seen=True,
        )
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('api_me'))
        self.assertEqual(response.data['unread_count'], 0)

    def test_mensaje_leido_no_cuenta(self):
        Message.objects.create(
            sender=self.otro, receiver=self.usuario, text='hola', is_read=True,
        )
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('api_me'))
        self.assertEqual(response.data['unread_count'], 0)

    def test_no_cuenta_mensajes_enviados_por_el_propio_usuario(self):
        Message.objects.create(sender=self.usuario, receiver=self.otro, text='hola')
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('api_me'))
        self.assertEqual(response.data['unread_count'], 0)