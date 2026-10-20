from itertools import count
from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase
from storages.backends.s3 import S3Storage

from core.imagenes.almacenamiento import CACHE_CONTROL, TigrisStorage


class UrlEstableTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.storage = TigrisStorage(
            bucket_name='prueba', access_key='x', secret_key='y',
            endpoint_url='https://t3.storage.dev', region_name='auto',
        )
        firmas = count()
        # Cada firma real sería distinta: se simula con un contador.
        parche = patch.object(
            S3Storage, 'url', autospec=True,
            side_effect=lambda _self, name, parameters=None, expire=None, http_method=None: (
                f'https://firmada/{name}?firma={next(firmas)}'
            ),
        )
        self.firmar = parche.start()
        self.addCleanup(parche.stop)

    def test_reutiliza_la_misma_url_entre_peticiones(self):
        self.assertEqual(self.storage.url('portada.jpg'), self.storage.url('portada.jpg'))
        self.assertEqual(self.firmar.call_count, 1)

    def test_firma_con_cache_control(self):
        self.storage.url('portada.jpg')
        self.assertEqual(self.firmar.call_args.kwargs['parameters'], {'ResponseCacheControl': CACHE_CONTROL})

    def test_cada_imagen_tiene_su_url(self):
        self.assertNotEqual(self.storage.url('a.jpg'), self.storage.url('b.jpg'))

    def test_borrar_descarta_la_url_guardada(self):
        antes = self.storage.url('portada.jpg')
        with patch.object(S3Storage, 'delete'):
            self.storage.delete('portada.jpg')
        self.assertNotEqual(self.storage.url('portada.jpg'), antes)

    def test_con_opciones_propias_firma_de_nuevo(self):
        self.storage.url('portada.jpg')
        self.storage.url('portada.jpg', expire=60)
        self.assertEqual(self.firmar.call_count, 2)