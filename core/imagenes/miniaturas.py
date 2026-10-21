"""Miniaturas de 400 px en WebP junto al original (portada.jpg → portada.min.webp),
para lo que se pinta pequeño: lomos, avatares, teselas y selectores."""

import logging
import posixpath
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

LADO_MINIATURA = 400
CALIDAD_MINIATURA = 78
SUFIJO = '.min.webp'


def nombre_miniatura(nombre):
    base, _ = posixpath.splitext(nombre)
    return base + SUFIJO


def generar_miniatura(datos):
    """WebP de LADO_MINIATURA como máximo. Si no se puede reducir (animada, formato raro),
    los bytes originales: la miniatura existe siempre y nunca se ve una imagen rota."""
    try:
        imagen = Image.open(BytesIO(datos))
        if getattr(imagen, 'is_animated', False):
            return datos
        imagen = ImageOps.exif_transpose(imagen)
        imagen.thumbnail((LADO_MINIATURA, LADO_MINIATURA), Image.Resampling.LANCZOS)
        if imagen.mode not in ('RGB', 'RGBA'):
            imagen = imagen.convert('RGBA' if imagen.mode in ('LA', 'P', 'PA') else 'RGB')
        salida = BytesIO()
        imagen.save(salida, 'WEBP', quality=CALIDAD_MINIATURA, method=4)
        return salida.getvalue()
    except (OSError, ValueError, Image.DecompressionBombError):
        return datos


def guardar_miniatura(storage, nombre_original, datos):
    """Escribe la miniatura de una imagen ya guardada (nombre relativo al almacenamiento).
    True si se guardó. Nunca lanza: un fallo no debe impedir publicar."""
    try:
        nombre = nombre_miniatura(nombre_original)
        miniatura = generar_miniatura(datos)
        guardado = storage.save(nombre, ContentFile(miniatura))
        # Nombre ocupado (raro: original nuevo implica miniatura nueva): se sustituye la anterior.
        if guardado != nombre:
            storage.delete(guardado)
            storage.delete(nombre)
            storage.save(nombre, ContentFile(miniatura))
        return True
    except Exception:
        logger.exception('No se pudo guardar la miniatura de %s', nombre_original)
        return False


def url_miniatura(archivo):
    """URL de la miniatura de un campo de imagen, o None si no hay archivo."""
    if not archivo:
        return None
    try:
        return archivo.storage.url(nombre_miniatura(archivo.name))
    except ValueError:
        return None