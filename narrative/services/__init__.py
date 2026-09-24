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
    """Se lanza cuando un avance de progreso supera el umbral de salto
    grande y no ha sido confirmado explícitamente por el usuario."""

    def __init__(self, orden_actual, orden_nuevo):
        self.orden_actual = orden_actual
        self.orden_nuevo = orden_nuevo
        self.salto = orden_nuevo - orden_actual
        super().__init__(
            f'El salto de progreso ({self.salto} posiciones) requiere confirmación explícita.'
        )


def calcular_orden_absoluto(unidad):
    """Progreso conservador a nivel de bloque: si no es hoja, se asume que
    todavía no se ha consumido nada de ese bloque."""
    if unidad.es_hoja:
        return unidad.orden_inicio
    return max(unidad.orden_inicio - 1, 0)


def actualizar_progreso(usuario, obra, nueva_unidad, confirmado=False):
    from ..models import ProgresoUsuario

    nuevo_orden = calcular_orden_absoluto(nueva_unidad)

    progreso, creado = ProgresoUsuario.objects.get_or_create(
        usuario=usuario,
        obra=obra,
        defaults={'unidad_actual': nueva_unidad, 'orden_absoluto': nuevo_orden},
    )
    if creado:
        return progreso

    if nuevo_orden < progreso.orden_absoluto:
        raise ValueError('El progreso no puede retroceder.')

    salto = nuevo_orden - progreso.orden_absoluto
    if salto > UMBRAL_SALTO_GRANDE and not confirmado:
        raise SaltoGrandeRequiereConfirmacion(progreso.orden_absoluto, nuevo_orden)

    progreso.unidad_actual = nueva_unidad
    progreso.orden_absoluto = nuevo_orden
    progreso.save(update_fields=['unidad_actual', 'orden_absoluto'])
    return progreso


def detectar_posibles_referencias_cruzadas(texto, obra):
    """Detección por palabra exacta (case-insensitive, límite de palabra)
    de menciones a una continuidad relacionada distinta de `obra`. No es
    infalible por diseño (falsos positivos posibles con esta técnica) —
    el usuario siempre puede confirmar la frontera real o descartar la
    detección como coincidencia antes de publicar. Solo compara contra
    obras realmente relacionadas (adapta_a en cualquier dirección),
    nunca contra el catálogo entero."""
    relacionadas = Obra.objects.filter(
        Q(adapta_a=obra) | Q(id=obra.adapta_a_id)
    ).exclude(id=obra.id)

    texto_lower = texto.lower()
    detecciones = []
    for relacionada in relacionadas:
        for palabra in TIPO_PALABRAS_CLAVE.get(relacionada.tipo, []):
            if re.search(rf'\b{re.escape(palabra)}\b', texto_lower):
                detecciones.append({'obra': relacionada, 'palabra': palabra})
                break
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