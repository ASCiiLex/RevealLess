import re

from django.db.models import Q
from django.utils import timezone

from ..models import Obra, SolicitudTema, TemaTransversal

UMBRAL_SALTO_GRANDE = 3

TIPO_PALABRAS_CLAVE = {
    Obra.TIPO_MANGA: ['manga'],
    Obra.TIPO_LIBRO: ['libro', 'novela'],
    Obra.TIPO_PELICULA: ['película', 'pelicula', 'film'],
    Obra.TIPO_SERIE: ['anime', 'serie'],
    Obra.TIPO_OVA: ['ova'],
    Obra.TIPO_ESPECIAL: [],
    Obra.TIPO_CORTO: [],
}


class SaltoGrandeRequiereConfirmacion(Exception):
    """Cambio de progreso que exige confirmación explícita: un avance mayor que el
    umbral o un retroceso permitido (salto negativo)."""

    def __init__(self, orden_actual, orden_nuevo):
        self.orden_actual = orden_actual
        self.orden_nuevo = orden_nuevo
        self.salto = orden_nuevo - orden_actual
        if self.salto < 0:
            mensaje = (
                f'Vas a retroceder {-self.salto} posiciones: '
                'lo que viene después volverá a ocultarse.'
            )
        else:
            mensaje = f'El salto de progreso ({self.salto} posiciones) requiere confirmación explícita.'
        super().__init__(mensaje)


def calcular_orden_absoluto(unidad):
    """Progreso conservador a nivel de bloque: si no es hoja, se asume que
    todavía no se ha consumido nada de ese bloque."""
    if unidad.es_hoja:
        return unidad.orden_inicio
    return max(unidad.orden_inicio - 1, 0)


def actualizar_progreso(usuario, obra, nueva_unidad, confirmado=False, permitir_retroceso=False):
    """permitir_retroceso: solo desde la gestión explícita de progreso (corregir un error).
    Publicar nunca retrocede: ocultaría contenido como efecto secundario."""
    from ..models import ProgresoUsuario

    nuevo_orden = calcular_orden_absoluto(nueva_unidad)

    progreso, creado = ProgresoUsuario.objects.get_or_create(
        usuario=usuario,
        obra=obra,
        defaults={'unidad_actual': nueva_unidad, 'orden_absoluto': nuevo_orden},
    )
    if creado:
        return progreso

    salto = nuevo_orden - progreso.orden_absoluto
    if salto < 0 and not permitir_retroceso:
        raise ValueError('El progreso no puede retroceder.')
    if not confirmado and (salto < 0 or salto > UMBRAL_SALTO_GRANDE):
        raise SaltoGrandeRequiereConfirmacion(progreso.orden_absoluto, nuevo_orden)

    progreso.unidad_actual = nueva_unidad
    progreso.orden_absoluto = nuevo_orden
    progreso.save(update_fields=['unidad_actual', 'orden_absoluto'])
    return progreso


def detectar_posibles_referencias_cruzadas(texto, obra):
    """Detección heurística de menciones a una obra relacionada distinta
    de `obra`. No es infalible por diseño — el usuario siempre puede
    confirmar la frontera real o descartar la detección antes de
    publicar. Dos fuentes de relación, cada una con su propio heurístico:

    - adapta_a (pool pequeño, normalmente 1 candidata): coincidencia por
      palabra clave genérica del tipo de la obra relacionada (comportamiento
      original, sin cambios).
    - Categoria compartida (pool potencialmente grande, ej. Marvel): una
      palabra genérica por tipo generaría ruido indiscriminado, así que se
      exige coincidencia por el título concreto de la obra candidata."""
    relacionadas_adapta = Obra.objects.filter(
        Q(adapta_a=obra) | Q(id=obra.adapta_a_id)
    ).exclude(id=obra.id)

    relacionadas_categoria = Obra.objects.filter(
        categorias__in=obra.categorias.all()
    ).exclude(id=obra.id).exclude(id__in=relacionadas_adapta.values('id')).distinct()

    texto_lower = texto.lower()
    detecciones = []

    for relacionada in relacionadas_adapta:
        for palabra in TIPO_PALABRAS_CLAVE.get(relacionada.tipo, []):
            if re.search(rf'\b{re.escape(palabra)}\b', texto_lower):
                detecciones.append({'obra': relacionada, 'palabra': palabra})
                break

    for relacionada in relacionadas_categoria:
        titulo_lower = relacionada.titulo.lower()
        if re.search(rf'\b{re.escape(titulo_lower)}\b', texto_lower):
            detecciones.append({'obra': relacionada, 'palabra': relacionada.titulo})

    return detecciones


def aprobar_solicitud_tema(solicitud):
    """Lógica pura de aprobación, sin dependencias de Django admin o
    HttpRequest: crea (o reutiliza, vía get_or_create) el TemaTransversal
    real y marca la solicitud como aprobada. Ignora solicitudes que ya
    no están pendientes (no las reabre ni las modifica).

    Devuelve el TemaTransversal creado/reutilizado, o None si la
    solicitud no estaba pendiente."""
    if solicitud.estado != SolicitudTema.ESTADO_PENDIENTE:
        return None

    tema, _ = TemaTransversal.objects.get_or_create(
        obra=solicitud.obra, nombre=solicitud.nombre,
    )
    solicitud.estado = SolicitudTema.ESTADO_APROBADA
    solicitud.resuelto_en = timezone.now()
    solicitud.save(update_fields=['estado', 'resuelto_en'])
    return tema


def rechazar_solicitud_tema(solicitud):
    """Lógica pura de rechazo. Ignora solicitudes que ya no están
    pendientes. Devuelve True si se rechazó, False si no aplicaba."""
    if solicitud.estado != SolicitudTema.ESTADO_PENDIENTE:
        return False

    solicitud.estado = SolicitudTema.ESTADO_RECHAZADA
    solicitud.resuelto_en = timezone.now()
    solicitud.save(update_fields=['estado', 'resuelto_en'])
    return True