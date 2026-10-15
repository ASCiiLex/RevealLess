from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from narrative.ai_assistant import Revelacion, SugerenciaIA
from narrative.services import actualizar_progreso
from .utils import crear_obra

PROPONER = 'posts.api_views.sugerir.proponer_clasificacion'
HECHO = 'Tobi es Obito'


class SugerirFronteraAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user('sugerencias', password='x')
        self.obra, self.ep = crear_obra('serie-sugerir', 3)
        self.url = reverse('posts_api_sugerir_frontera', args=[self.obra.slug])
        self.client.force_authenticate(user=self.usuario)

    def _con_progreso(self):
        actualizar_progreso(self.usuario, self.obra, self.ep[2])

    def _sugerencia(self, confianza=0.9):
        return SugerenciaIA(self.ep[2], confianza, self.ep[0], [Revelacion(HECHO, self.ep[2], confianza)])

    def test_devuelve_la_frontera_y_pasa_la_parte_a_la_ia(self):
        self._con_progreso()
        with patch(PROPONER, return_value=self._sugerencia()) as proponer:
            response = self.client.post(self.url, {'text': 'escena', 'referencia_narrativa': self.ep[0].id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['frontera']['id'], self.ep[2].id)
        self.assertTrue(response.data['fiable'])
        self.assertIsNone(response.data['parte'])
        self.assertEqual(proponer.call_args.args[2], self.ep[0])

    def test_nunca_expone_los_hechos_revelados(self):
        self._con_progreso()
        for confianza in (0.9, 0.3):
            with patch(PROPONER, return_value=self._sugerencia(confianza)):
                response = self.client.post(self.url, {'text': 'escena'})
            self.assertNotIn(HECHO, response.content.decode())

    def test_sin_parte_elegida_propone_la_parte(self):
        self._con_progreso()
        with patch(PROPONER, return_value=self._sugerencia()):
            response = self.client.post(self.url, {'text': 'escena'})
        self.assertEqual(response.data['parte']['id'], self.ep[0].id)

    def test_confianza_baja_propone_pero_no_es_fiable(self):
        self._con_progreso()
        with patch(PROPONER, return_value=self._sugerencia(0.3)):
            response = self.client.post(self.url, {'text': 'escena'})
        self.assertEqual(response.data['frontera']['id'], self.ep[2].id)
        self.assertFalse(response.data['fiable'])

    def test_fallo_de_la_ia_no_propone_nada(self):
        self._con_progreso()
        with patch(PROPONER, return_value=SugerenciaIA()):
            response = self.client.post(self.url, {'text': 'escena'})
        self.assertIsNone(response.data['frontera'])
        self.assertIsNone(response.data['parte'])
        self.assertFalse(response.data['fiable'])

    def test_obra_cruzada_basta_con_progreso_en_la_obra_desde_la_que_se_publica(self):
        otra, otra_ep = crear_obra('serie-sugerir-otra', 2)
        self._con_progreso()
        url = reverse('posts_api_sugerir_frontera', args=[otra.slug])
        with patch(PROPONER, return_value=SugerenciaIA(otra_ep[1], 0.8, otra_ep[0])):
            response = self.client.post(url, {'text': 'escena', 'desde': self.obra.slug})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['frontera']['id'], otra_ep[1].id)

    def test_obra_cruzada_sin_progreso_en_ninguna_devuelve_409(self):
        otra, _ = crear_obra('serie-sugerir-otra', 2)
        url = reverse('posts_api_sugerir_frontera', args=[otra.slug])
        response = self.client.post(url, {'text': 'escena', 'desde': self.obra.slug})
        self.assertEqual(response.status_code, 409)

    def test_sin_texto_devuelve_400(self):
        self._con_progreso()
        self.assertEqual(self.client.post(self.url, {'text': '  '}).status_code, 400)

    def test_sin_progreso_devuelve_409(self):
        response = self.client.post(self.url, {'text': 'escena'})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['detail'], 'progreso_requerido')