"""Versiones reducidas en WebP junto al original (portada.jpg → portada.min.webp, portada.med.webp):
min para lo que se pinta pequeño (lomos, avatares, teselas); med para fotos del feed y cabeceras."""

import logging
import posixpath
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

VARIANTES = {'min': 400, 'med': 900}
LADO_MINIATURA = VARIANTES['min']
CALIDAD_VARIANTE = 78


def nombre_variante(nombre, variante):
    base, _ = posixpath.splitext(nombre)
    return f'{base}.{variante}.webp'


def nombre_miniatura(nombre):
    return nombre_variante(nombre, 'min')


def generar_variante(datos, lado):
    """WebP de `lado` px como máximo. Si no se puede reducir (animada, formato raro),
    los bytes originales: la variante existe siempre y nunca se ve una imagen rota."""
    try:
        imagen = Image.open(BytesIO(datos))
        if getattr(imagen, 'is_animated', False):
            return datos
        imagen = ImageOps.exif_transpose(imagen)
        imagen.thumbnail((lado, lado), Image.Resampling.LANCZOS)
        if imagen.mode not in ('RGB', 'RGBA'):
            imagen = imagen.convert('RGBA' if imagen.mode in ('LA', 'P', 'PA') else 'RGB')
        salida = BytesIO()
        imagen.save(salida, 'WEBP', quality=CALIDAD_VARIANTE, method=4)
        return salida.getvalue()
    except (OSError, ValueError, Image.DecompressionBombError):
        return datos


def generar_miniatura(datos):
    return generar_variante(datos, LADO_MINIATURA)


def guardar_variantes(storage, nombre_original, datos, variantes=None):
    """Escribe las variantes indicadas (todas por defecto) de una imagen ya guardada.
    True si se guardaron todas. Nunca lanza: un fallo no debe impedir publicar."""
    completas = True
    for variante in variantes or VARIANTES:
        try:
            nombre = nombre_variante(nombre_original, variante)
            contenido = generar_variante(datos, VARIANTES[variante])
            guardado = storage.save(nombre, ContentFile(contenido))
            # Nombre ocupado (raro: original nuevo implica variantes nuevas): se sustituye la anterior.
            if guardado != nombre:
                storage.delete(guardado)
                storage.delete(nombre)
                storage.save(nombre, ContentFile(contenido))
        except Exception:
            logger.exception('No se pudo guardar la variante %s de %s', variante, nombre_original)
            completas = False
    return completas


def url_variante(archivo, variante):
    """URL de una variante de un campo de imagen, o None si no hay archivo."""
    if not archivo:
        return None
    try:
        return archivo.storage.url(nombre_variante(archivo.name, variante))
    except ValueError:
        return None


def url_miniatura(archivo):
    return url_variante(archivo, 'min')