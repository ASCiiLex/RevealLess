import hashlib
import threading

from django.core.cache import cache
from storages.backends.s3 import S3Storage

# La firma dura 6 h (querystring_expire): reutilizada 5 h, a cualquier URL servida le queda al menos 1 h.
VIDA_URL_REUTILIZADA = 5 * 60 * 60
CACHE_CONTROL = 'private, max-age=21600'


def _clave_url(nombre):
    return 'tigris-url:' + hashlib.sha256(nombre.encode()).hexdigest()


class TigrisStorage(S3Storage):
    """S3Storage guarda la conexión por hilo; bajo ASGI cada petición corre en un hilo nuevo y
    recrearla (sesión boto3 + modelos del servicio) cuesta cientos de ms. Se comparte por proceso:
    firmar URLs es cálculo local y las subidas usan el cliente de boto3, que es seguro entre hilos.

    La URL firmada se reutiliza entre peticiones: firmar en cada una cambiaba la URL y el
    navegador nunca podía usar su caché."""

    _conexion = None
    _cerrojo = threading.Lock()

    @property
    def connection(self):
        if TigrisStorage._conexion is None:
            with TigrisStorage._cerrojo:
                if TigrisStorage._conexion is None:
                    TigrisStorage._conexion = super().connection
        return TigrisStorage._conexion

    def url(self, name, parameters=None, expire=None, http_method=None):
        # Peticiones con opciones propias: firma nueva, sin reutilizar.
        if parameters or expire or http_method:
            return super().url(name, parameters, expire, http_method)
        clave = _clave_url(name)
        url = cache.get(clave)
        if url is None:
            # Cache-Control en la respuesta firmada: vale también para imágenes subidas sin esa cabecera.
            url = super().url(name, parameters={'ResponseCacheControl': CACHE_CONTROL})
            cache.set(clave, url, VIDA_URL_REUTILIZADA)
        return url

    def delete(self, name):
        super().delete(name)
        cache.delete(_clave_url(name))