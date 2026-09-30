"""Descarga de imágenes desde una URL externa (portadas en el admin).

Solo http(s), solo hosts públicos (también en cada redirección, contra SSRF),
tipo jpg/png/webp y tamaño máximo común a las subidas locales."""

import ipaddress
import socket
import urllib.error
import urllib.request
from io import BytesIO
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image

from .validators import MAX_IMAGE_SIZE_MB

TIPOS_PERMITIDOS = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp'}
MAX_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
TIMEOUT_S = 10


def _host_publico(host):
    try:
        direcciones = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except socket.gaierror as e:
        raise ValidationError('No se pudo resolver el dominio del enlace.') from e
    return all(ipaddress.ip_address(ip).is_global for ip in direcciones)


def validar_url(url):
    partes = urlparse(url)
    if partes.scheme not in ('http', 'https') or not partes.hostname:
        raise ValidationError('Solo se admiten enlaces http o https.')
    if not _host_publico(partes.hostname):
        raise ValidationError('El enlace apunta a una dirección no pública.')


class _RedireccionSegura(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validar_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _abrir(url):
    """Devuelve (content_type, bytes leídos hasta MAX_BYTES + 1)."""
    opener = urllib.request.build_opener(_RedireccionSegura)
    peticion = urllib.request.Request(url, headers={'User-Agent': 'RevealLess/1.0'})
    with opener.open(peticion, timeout=TIMEOUT_S) as respuesta:
        return respuesta.headers.get_content_type(), respuesta.read(MAX_BYTES + 1)


def descargar_imagen(url):
    validar_url(url)

    try:
        tipo, datos = _abrir(url)
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        raise ValidationError('No se pudo descargar la imagen del enlace.') from e

    if tipo not in TIPOS_PERMITIDOS:
        raise ValidationError('El enlace no es una imagen jpg, png o webp.')
    if len(datos) > MAX_BYTES:
        raise ValidationError(f'La imagen no puede superar {MAX_IMAGE_SIZE_MB} MB.')

    try:
        Image.open(BytesIO(datos)).verify()
    except Exception as e:
        raise ValidationError('El archivo descargado no es una imagen válida.') from e

    return ContentFile(datos, name=f'portada.{TIPOS_PERMITIDOS[tipo]}')