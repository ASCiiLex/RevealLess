from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Message


class InboxListAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('inbox_user', password='x')
        self.otro = User.objects.create_user('inbox_otro', password='x')
        self.tercero = User.objects.create_user('inbox_tercero', password='x')

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('messages_api_inbox'))
        self.assertEqual(response.status_code, 403)

    def test_lista_conversaciones_del_usuario(self):
        Message.objects.create(sender=self.usuario, receiver=self.otro, text='hola')

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('messages_api_inbox'))
        usernames = [u['username'] for u in response.data]
        self.assertIn('inbox_otro', usernames)
        self.assertNotIn('inbox_tercero', usernames)

    def test_incluye_ultimo_mensaje_y_no_leidos(self):
        Message.objects.create(sender=self.otro, receiver=self.usuario, text='primero')
        Message.objects.create(sender=self.otro, receiver=self.usuario, text='segundo, el ultimo')

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('messages_api_inbox'))
        item = response.data[0]
        self.assertEqual(item['last_message'], 'segundo, el ultimo')
        self.assertEqual(item['unread_count'], 2)

    def test_ultimo_mensaje_aunque_sea_propio(self):
        Message.objects.create(sender=self.otro, receiver=self.usuario, text='pregunta')
        Message.objects.create(sender=self.usuario, receiver=self.otro, text='mi respuesta')

        self.client.force_authenticate(user=self.usuario)
        item = self.client.get(reverse('messages_api_inbox')).data[0]
        self.assertEqual(item['last_message'], 'mi respuesta')
        self.assertEqual(item['unread_count'], 1)

    def test_conversaciones_ordenadas_por_ultimo_mensaje(self):
        Message.objects.create(sender=self.usuario, receiver=self.tercero, text='mas antiguo')
        Message.objects.create(sender=self.usuario, receiver=self.otro, text='mas reciente')

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('messages_api_inbox'))
        usernames = [u['username'] for u in response.data]
        self.assertEqual(usernames[0], 'inbox_otro')

    def test_las_consultas_no_crecen_con_las_conversaciones(self):
        self.client.force_authenticate(user=self.usuario)
        Message.objects.create(sender=self.otro, receiver=self.usuario, text='a')

        def consultas():
            with CaptureQueriesContext(connection) as capturadas:
                self.client.get(reverse('messages_api_inbox'))
            return len(capturadas)

        antes = consultas()
        for i in range(3):
            extra = User.objects.create_user(f'inbox_extra_{i}', password='x')
            Message.objects.create(sender=extra, receiver=self.usuario, text='b')
        self.assertEqual(consultas(), antes)


class ChatHistoryAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('chat_user', password='x')
        self.otro = User.objects.create_user('chat_otro', password='x')

    def test_requiere_autenticacion(self):
        response = self.client.get(reverse('messages_api_chat', args=['chat_otro']))
        self.assertEqual(response.status_code, 403)

    def test_devuelve_historial_completo(self):
        Message.objects.create(sender=self.usuario, receiver=self.otro, text='hola')
        Message.objects.create(sender=self.otro, receiver=self.usuario, text='que tal')

        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('messages_api_chat', args=['chat_otro']))
        self.assertEqual(len(response.data['messages']), 2)

    def test_marca_como_leidos_los_mensajes_recibidos(self):
        Message.objects.create(sender=self.otro, receiver=self.usuario, text='sin leer', is_read=False)

        self.client.force_authenticate(user=self.usuario)
        self.client.get(reverse('messages_api_chat', args=['chat_otro']))

        self.assertFalse(
            Message.objects.filter(receiver=self.usuario, is_read=False).exists()
        )

    def test_rechaza_chatear_con_uno_mismo(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('messages_api_chat', args=['chat_user']))
        self.assertEqual(response.status_code, 400)

    def test_devuelve_404_si_el_otro_usuario_no_existe(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('messages_api_chat', args=['no_existe']))
        self.assertEqual(response.status_code, 404)

    def test_incluye_datos_del_otro_usuario(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(reverse('messages_api_chat', args=['chat_otro']))
        self.assertEqual(response.data['other']['username'], 'chat_otro')