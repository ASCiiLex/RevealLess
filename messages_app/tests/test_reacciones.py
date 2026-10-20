from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from ..models import Message, MessageReaction
from ..salas import sala_chat


class ReaccionMensajeTests(TestCase):
    def setUp(self):
        self.remitente = User.objects.create_user('remitente', password='x')
        self.destinatario = User.objects.create_user('destinatario', password='x')
        self.tercero = User.objects.create_user('tercero', password='x')
        self.mensaje = Message.objects.create(sender=self.remitente, receiver=self.destinatario, text='hola')
        self.url = reverse('toggle_reaction_message', args=[self.mensaje.id])

    def _reaccionar(self, usuario, reaccion='me_gusta'):
        self.client.force_login(usuario)
        return self.client.post(self.url, {'reaction': reaccion})

    def test_el_destinatario_reacciona(self):
        response = self._reaccionar(self.destinatario)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['reaccion'], 'me_gusta')
        self.assertTrue(MessageReaction.objects.filter(user=self.destinatario, message=self.mensaje).exists())

    def test_el_remitente_no_puede_reaccionar(self):
        self.assertEqual(self._reaccionar(self.remitente).status_code, 403)
        self.assertFalse(MessageReaction.objects.exists())

    def test_un_tercero_no_puede_reaccionar(self):
        self.assertEqual(self._reaccionar(self.tercero).status_code, 403)

    def test_repetir_la_misma_reaccion_la_quita(self):
        self._reaccionar(self.destinatario)
        response = self._reaccionar(self.destinatario)
        self.assertIsNone(response.json()['reaccion'])
        self.assertFalse(MessageReaction.objects.exists())

    def test_otra_reaccion_sustituye_a_la_anterior(self):
        self._reaccionar(self.destinatario)
        self._reaccionar(self.destinatario, 'me_encanta')
        self.assertEqual(MessageReaction.objects.get().reaction, 'me_encanta')

    def test_reaccion_no_valida(self):
        self.assertEqual(self._reaccionar(self.destinatario, 'no_existe').status_code, 400)

    def test_avisa_a_la_sala_del_chat_en_tiempo_real(self):
        with mock.patch('messages_app.views.get_channel_layer') as obtener_capa:
            obtener_capa.return_value.group_send = mock.AsyncMock()
            self._reaccionar(self.destinatario)
        obtener_capa.return_value.group_send.assert_awaited_once_with(
            sala_chat('remitente', 'destinatario'),
            {'type': 'reaction_message', 'data': {'message_id': self.mensaje.id, 'reaccion': 'me_gusta'}},
        )


class HistorialReaccionTests(TestCase):
    def test_el_historial_trae_solo_la_reaccion_del_destinatario(self):
        remitente = User.objects.create_user('rem', password='x')
        destinatario = User.objects.create_user('dest', password='x')
        mensaje = Message.objects.create(sender=remitente, receiver=destinatario, text='hola')
        # Reacción del remitente anterior al cambio de regla: se ignora.
        MessageReaction.objects.create(user=remitente, message=mensaje, reaction='me_divierte')
        MessageReaction.objects.create(user=destinatario, message=mensaje, reaction='me_encanta')

        cliente = APIClient()
        cliente.force_authenticate(user=remitente)
        response = cliente.get(reverse('messages_api_chat', args=['dest']))
        self.assertEqual(response.data['messages'][0]['reaccion'], 'me_encanta')


class SalaChatTests(TestCase):
    def test_mismo_nombre_sea_cual_sea_el_orden(self):
        self.assertEqual(sala_chat('ana', 'bea'), sala_chat('bea', 'ana'))