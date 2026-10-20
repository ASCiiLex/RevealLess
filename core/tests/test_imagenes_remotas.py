from io import BytesIO
from unittest import mock

import pytest
from django.core.exceptions import ValidationError
from PIL import Image

from core import imagenes_remotas
from core.imagenes_remotas import descargar_imagen


def _png():
    buffer = BytesIO()
    Image.new('RGB', (4, 4), 'white').save(buffer, format='PNG')
    return buffer.getvalue()


@pytest.fixture
def host_publico():
    with mock.patch.object(imagenes_remotas, '_host_publico', return_value=True):
        yield


def test_rechaza_esquemas_no_http():
    with pytest.raises(ValidationError):
        descargar_imagen('ftp://ejemplo.com/portada.png')


def test_rechaza_hosts_no_publicos():
    with pytest.raises(ValidationError):
        descargar_imagen('http://127.0.0.1/portada.png')


def test_rechaza_contenido_que_no_es_imagen(host_publico):
    with mock.patch.object(imagenes_remotas, '_abrir', return_value=('text/html', b'<html>')):
        with pytest.raises(ValidationError):
            descargar_imagen('https://ejemplo.com/portada')


def test_rechaza_imagen_demasiado_grande(host_publico):
    datos = b'0' * (imagenes_remotas.MAX_BYTES + 1)
    with mock.patch.object(imagenes_remotas, '_abrir', return_value=('image/png', datos)):
        with pytest.raises(ValidationError):
            descargar_imagen('https://ejemplo.com/portada.png')


def test_rechaza_bytes_que_no_son_una_imagen_valida(host_publico):
    with mock.patch.object(imagenes_remotas, '_abrir', return_value=('image/png', b'no-es-png')):
        with pytest.raises(ValidationError):
            descargar_imagen('https://ejemplo.com/portada.png')


def test_descarga_valida_devuelve_archivo_con_extension(host_publico):
    with mock.patch.object(imagenes_remotas, '_abrir', return_value=('image/png', _png())):
        archivo = descargar_imagen('https://ejemplo.com/portada')
    assert archivo.name == 'portada.png'
    assert archivo.size > 0