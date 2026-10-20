"""Contadores del menú lateral del admin. None oculta el contador."""

from narrative.models import PropuestaAparicion, SolicitudObra, SolicitudPersonaje, SolicitudTema


def _pendientes(modelo):
    return modelo.objects.filter(estado=modelo.ESTADO_PENDIENTE).count() or None


def solicitudes_obra_pendientes(request):
    return _pendientes(SolicitudObra)


def solicitudes_tema_pendientes(request):
    return _pendientes(SolicitudTema)


def solicitudes_personaje_pendientes(request):
    return _pendientes(SolicitudPersonaje)


def propuestas_aparicion_pendientes(request):
    return _pendientes(PropuestaAparicion)