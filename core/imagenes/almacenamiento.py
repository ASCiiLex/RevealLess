import hashlib
import posixpath
import threading

from django.core.cache import cache
from storages.backends.s3 import S3Storage

# La firma dura 6 h (querystring_expire): reutilizada 5 h, a cualquier URL servida le queda al menos 1 h.
VIDA_URL_REUTILIZADA = 5 * 60 * 60
CACHE_CONTROL = 'private, max-age=21600'
# Tipo forzado en la respuesta: corrige las imágenes que se subieron como octet-stream.
TIPOS_IMAGEN = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp',
}


def _clave_url(nombre):
    # v2: las URLs guardadas antes no llevaban el tipo de contenido.
    return 'tigris-url-v2:' + hashlib.sha256(nombre.encode()).hexdigest()


def parametros_respuesta(nombre):
    parametros = {'ResponseCacheControl': CACHE_CONTROL}
    tipo = TIPOS_IMAGEN.get(posixpath.splitext(nombre)[1].lower())
    if tipo:
        parametros['ResponseContentType'] = tipo
    return parametros


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
            # Cabeceras forzadas en la respuesta firmada: valen también para lo ya subido.
            url = super().url(name, parameters=parametros_respuesta(name))
            cache.set(clave, url, VIDA_URL_REUTILIZADA)
        return url

    def delete(self, name):
        super().delete(name)
        cache.delete(_clave_url(name))