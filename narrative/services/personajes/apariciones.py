"""Revisión de apariciones: solo una propuesta aprobada pasa a Personaje.unidades."""

from django.db import transaction
from django.utils import timezone

from ...models import PropuestaAparicion


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


@transaction.atomic
def aplicar_cambio_propuesta(propuesta, estado_anterior=None, unidad_anterior_id=None):
    """Sincroniza Personaje.unidades tras editar estado o unidad a mano (ya guardada).
    estado_anterior/unidad_anterior_id: valores en BD antes de guardar; None si es nueva."""
    if propuesta.estado == estado_anterior and propuesta.unidad_id == unidad_anterior_id:
        return propuesta
    if estado_anterior == PropuestaAparicion.ESTADO_APROBADA and unidad_anterior_id is not None:
        propuesta.personaje.unidades.remove(unidad_anterior_id)
    if propuesta.estado == PropuestaAparicion.ESTADO_APROBADA:
        return aprobar_propuesta(propuesta)
    if propuesta.estado == PropuestaAparicion.ESTADO_RECHAZADA:
        return rechazar_propuesta(propuesta)
    # Vuelta a pendiente.
    if propuesta.resuelto_en is not None:
        propuesta.resuelto_en = None
        propuesta.save(update_fields=['resuelto_en'])
    return propuesta


@transaction.atomic
def eliminar_propuesta(propuesta):
    if propuesta.estado == PropuestaAparicion.ESTADO_APROBADA:
        propuesta.personaje.unidades.remove(propuesta.unidad_id)
    propuesta.delete()