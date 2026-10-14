from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.ai_assistant import SugerenciaIA
from narrative.services import actualizar_progreso
from .utils import crear_obra

PROPONER = 'posts.api_views.sugerir.proponer_clasificacion'


class SugerirFronteraAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('sugerencias', password='x')
        self.obra, self.ep = crear_obra('serie-sugerir', 3)
        self.url = reverse('posts_api_sugerir_frontera', args=[self.obra.slug])
        self.client.force_authenticate(user=self.usuario)

    def _con_progreso(self):
        actualizar_progreso(self.usuario, self.obra, self.ep[2])

    def test_devuelve_la_propuesta_y_pasa_la_parte_a_la_ia(self):
        self._con_progreso()
        with patch(PROPONER, return_value=SugerenciaIA(self.ep[1], 0.9)) as proponer:
            response = self.client.post(self.url, {'text': 'escena', 'referencia_narrativa': self.ep[0].id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['frontera']['id'], self.ep[1].id)
        self.assertEqual(response.data['confianza'], 0.9)
        self.assertEqual(proponer.call_args.args[3], self.ep[0])

    def test_confianza_baja_no_propone_frontera(self):
        self._con_progreso()
        with patch(PROPONER, return_value=SugerenciaIA(self.ep[1], 0.3)):
            response = self.client.post(self.url, {'text': 'escena'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['frontera'])

    def test_sin_texto_devuelve_400(self):
        self._con_progreso()
        self.assertEqual(self.client.post(self.url, {'text': '  '}).status_code, 400)

    def test_sin_progreso_devuelve_409(self):
        response = self.client.post(self.url, {'text': 'escena'})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['detail'], 'progreso_requerido')