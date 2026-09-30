"""Personajes: revisión de apariciones y presentación según el progreso del lector."""

from datetime import date

from django.db import transaction
from django.utils import timezone

from ..models import ProgresoUsuario, PropuestaAparicion


@transaction.atomic
def aprobar_propuesta(propuesta):
    propuesta.personaje.unidades.add(propuesta.unidad)
    propuesta.estado = PropuestaAparicion.ESTADO_APROBADA
    propuesta.resuelto_en = timezone.now()
    propuesta.save(update_fields=['estado', 'resuelto_en'])
    return propuesta


@transaction.atomic
def rechazar_propuesta(propuesta):
    # Rechazar una ya aprobada la retira de las landings.
    propuesta.personaje.unidades.remove(propuesta.unidad)
    propuesta.estado = PropuestaAparicion.ESTADO_RECHAZADA
    propuesta.resuelto_en = timezone.now()
    propuesta.save(update_fields=['estado', 'resuelto_en'])
    return propuesta


def progreso_por_obra(usuario):
    return dict(ProgresoUsuario.objects.filter(usuario=usuario).values_list('obra_id', 'orden_absoluto'))


def _superada(etapa, progreso):
    unidad = etapa.visible_tras
    alcanzado = progreso.get(unidad.obra_id)
    return alcanzado is not None and alcanzado >= unidad.orden_fin


def presentacion_personaje(personaje, progreso, obra_id=None):
    """Nombre, imagen y nota que puede ver el lector. Acumula las etapas cuya unidad
    ya terminó; cada campo vacío hereda el anterior. Con obra_id solo cuentan las
    etapas de esa obra; sin él, todas, por fecha de su unidad.
    Conviene prefetch_related('etapas__visible_tras')."""
    etapas = [
        e for e in personaje.etapas.all()
        if _superada(e, progreso) and (obra_id is None or e.visible_tras.obra_id == obra_id)
    ]
    if obra_id is None:
        etapas.sort(key=lambda e: (e.visible_tras.fecha or date.min, e.visible_tras.orden_fin))
    else:
        etapas.sort(key=lambda e: e.visible_tras.orden_fin)

    datos = {'nombre': personaje.nombre, 'imagen_url': personaje.image_url, 'nota': None}
    for etapa in etapas:
        if etapa.alias:
            datos['nombre'] = etapa.alias
        if etapa.imagen:
            datos['imagen_url'] = etapa.imagen.url
        if etapa.nota:
            datos['nota'] = etapa.nota
    return datos