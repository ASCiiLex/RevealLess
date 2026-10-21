from functools import lru_cache
from io import BytesIO

from django.core.files.base import ContentFile
from django.db.models import ImageField
from PIL import Image, ImageOps

from .miniaturas import guardar_variantes

LADO_MAXIMO = 1600
# Por debajo de este peso (y del lado máximo) no se toca: recomprimir degradaría sin ganar nada.
PESO_MINIMO = 300 * 1024
CALIDAD = 82
# MPO: JPEG de varias capas que generan algunos móviles.
FORMATOS = {'JPEG': 'JPEG', 'MPO': 'JPEG', 'PNG': 'PNG', 'WEBP': 'WEBP'}
# Orientaciones EXIF que giran 90°: el navegador la muestra con ancho y alto intercambiados.
ORIENTACIONES_GIRADAS = {5, 6, 7, 8}
ETIQUETA_ORIENTACION = 0x0112


def optimizar_imagen(datos):
    """Bytes optimizados (orientación aplicada, sin EXIF, lado máximo y recomprimida),
    o None si no compensa, no es una imagen o es animada."""
    try:
        imagen = Image.open(BytesIO(datos))
        formato = FORMATOS.get(imagen.format)
        if formato is None or getattr(imagen, 'is_animated', False):
            return None
        grande = max(imagen.size) > LADO_MAXIMO
        if not grande and len(datos) <= PESO_MINIMO:
            return None

        perfil_color = imagen.info.get('icc_profile')
        imagen = ImageOps.exif_transpose(imagen)
        if grande:
            imagen.thumbnail((LADO_MAXIMO, LADO_MAXIMO), Image.Resampling.LANCZOS)

        # Sin pasar exif= al guardar, los metadatos (incluida la ubicación GPS) se descartan.
        salida = BytesIO()
        if formato == 'JPEG':
            if imagen.mode not in ('RGB', 'L'):
                imagen = imagen.convert('RGB')
            imagen.save(salida, 'JPEG', quality=CALIDAD, optimize=True, progressive=True, icc_profile=perfil_color)
        elif formato == 'WEBP':
            imagen.save(salida, 'WEBP', quality=CALIDAD, method=6, icc_profile=perfil_color)
        else:
            imagen.save(salida, 'PNG', optimize=True)
        resultado = salida.getvalue()
    except (OSError, ValueError, Image.DecompressionBombError):
        return None
    return resultado if len(resultado) < len(datos) else None


def medir_imagen(datos):
    """(ancho, alto) tal como se ve (orientación EXIF aplicada), o None si no es una imagen."""
    try:
        imagen = Image.open(BytesIO(datos))
        ancho, alto = imagen.size
        if imagen.getexif().get(ETIQUETA_ORIENTACION) in ORIENTACIONES_GIRADAS:
            return alto, ancho
        return ancho, alto
    except (OSError, ValueError, Image.DecompressionBombError):
        return None


@lru_cache(maxsize=None)
def campos_imagen(modelo):
    return tuple(f for f in modelo._meta.concrete_fields if isinstance(f, ImageField))


def optimizar_al_guardar(sender, instance, raw=False, **kwargs):
    """pre_save de cualquier modelo: optimiza las imágenes recién asignadas antes de subirlas
    y deja sus bytes para las variantes, que se crean cuando ya tienen nombre definitivo.
    Si el modelo declara DIMENSIONES_IMAGEN ({campo: (campo_ancho, campo_alto)}), guarda también sus medidas."""
    if raw:
        return
    dimensiones = getattr(sender, 'DIMENSIONES_IMAGEN', {})
    pendientes = []
    for campo in campos_imagen(sender):
        archivo = getattr(instance, campo.attname)
        if not archivo or getattr(archivo, '_committed', True):
            continue
        archivo.seek(0)
        datos = archivo.read()
        optimizada = optimizar_imagen(datos)
        if optimizada is None:
            archivo.seek(0)
        else:
            setattr(instance, campo.attname, ContentFile(optimizada, name=archivo.name))
            datos = optimizada
        pendientes.append((campo.attname, datos))

        if campo.attname in dimensiones:
            medidas = medir_imagen(datos)
            campo_ancho, campo_alto = dimensiones[campo.attname]
            setattr(instance, campo_ancho, medidas[0] if medidas else None)
            setattr(instance, campo_alto, medidas[1] if medidas else None)
    if pendientes:
        instance._miniaturas_pendientes = pendientes


def miniaturas_al_guardar(sender, instance, raw=False, **kwargs):
    """post_save: variantes de cada imagen recién subida, con los bytes que ya estaban en memoria."""
    pendientes = instance.__dict__.pop('_miniaturas_pendientes', None)
    if raw or not pendientes:
        return
    for attname, datos in pendientes:
        archivo = getattr(instance, attname)
        guardar_variantes(archivo.storage, archivo.name, datos)