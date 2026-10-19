import threading

from storages.backends.s3 import S3Storage


class TigrisStorage(S3Storage):
    """S3Storage guarda la conexión por hilo; bajo ASGI cada petición corre en un hilo nuevo y
    recrearla (sesión boto3 + modelos del servicio) cuesta cientos de ms. Se comparte por proceso:
    firmar URLs es cálculo local y las subidas usan el cliente de boto3, que es seguro entre hilos."""

    _conexion = None
    _cerrojo = threading.Lock()

    @property
    def connection(self):
        if TigrisStorage._conexion is None:
            with TigrisStorage._cerrojo:
                if TigrisStorage._conexion is None:
                    TigrisStorage._conexion = super().connection
        return TigrisStorage._conexion