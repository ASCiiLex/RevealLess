import threading

from django.test import SimpleTestCase

from core.almacenamiento import TigrisStorage


class TigrisStorageTests(SimpleTestCase):
    def setUp(self):
        TigrisStorage._conexion = None
        self.addCleanup(setattr, TigrisStorage, '_conexion', None)

    def _almacen(self):
        return TigrisStorage(
            bucket_name='prueba', access_key='a', secret_key='b',
            endpoint_url='https://t3.storage.dev', region_name='auto',
        )

    def test_la_conexion_se_comparte_entre_hilos(self):
        almacen = self._almacen()
        conexiones = []
        hilos = [threading.Thread(target=lambda: conexiones.append(almacen.connection)) for _ in range(3)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()
        self.assertEqual(len({id(c) for c in conexiones}), 1)

    def test_y_entre_instancias(self):
        self.assertIs(self._almacen().connection, self._almacen().connection)