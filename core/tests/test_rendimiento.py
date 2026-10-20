from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from core.rendimiento import RegistroLentitudMiddleware


class RegistroLentitudTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get('/narrative/api/feed/?page=1')
        self.middleware = RegistroLentitudMiddleware(lambda r: HttpResponse('ok'))

    @override_settings(RENDIMIENTO_UMBRAL_MS=0)
    def test_registra_las_peticiones_que_superan_el_umbral(self):
        with self.assertLogs('core.rendimiento', level='WARNING') as registro:
            response = self.middleware(self.request)
        self.assertEqual(response.content, b'ok')
        self.assertIn('/narrative/api/feed/?page=1', registro.output[0])
        self.assertIn('0 consultas', registro.output[0])

    @override_settings(RENDIMIENTO_UMBRAL_MS=60000)
    def test_no_registra_las_rapidas(self):
        with self.assertNoLogs('core.rendimiento', level='WARNING'):
            self.middleware(self.request)