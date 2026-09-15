from django.utils import timezone

from ..models import SolicitudTema, TemaTransversal

UMBRAL_SALTO_GRANDE = 3


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
        # Primera declaración de progreso: no es un "salto" respecto a nada,
        # así que no exige confirmación aunque el punto de partida sea alto.
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