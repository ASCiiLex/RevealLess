"""Personajes propuestos por usuarios al publicar una comparativa."""

from django.db import transaction
from django.utils import timezone

from ...models import Personaje, PropuestaAparicion, SolicitudPersonaje
from .apariciones import aprobar_propuesta


def proponer_personaje(obra, unidad, usuario, nombre):
    """Personaje propuesto al publicar. Reutiliza la solicitud pendiente con el mismo
    nombre en la obra: varios posts pueden esperar al mismo personaje."""
    nombre = ' '.join(nombre.split())[:150]
    pendiente = SolicitudPersonaje.objects.filter(
        obra=obra, nombre__iexact=nombre, estado=SolicitudPersonaje.ESTADO_PENDIENTE,
    ).first()
    if pendiente:
        return pendiente
    return SolicitudPersonaje.objects.create(obra=obra, unidad=unidad, usuario=usuario, nombre=nombre)


@transaction.atomic
def aprobar_solicitud_personaje(solicitud):
    """Crea o reutiliza el personaje (el elegido en la solicitud, o el que coincida por nombre),
    aprueba su aparición en la unidad de la solicitud y lo vincula a los posts que lo propusieron.
    Devuelve el personaje, o None si la solicitud no estaba pendiente."""
    from posts.models import PersonajeComparado  # import diferido: posts depende de narrative

    if solicitud.estado != SolicitudPersonaje.ESTADO_PENDIENTE:
        return None

    personaje = (
        solicitud.personaje
        or Personaje.objects.filter(nombre__iexact=solicitud.nombre).first()
        or Personaje.objects.create(nombre=solicitud.nombre)
    )
    propuesta, _ = PropuestaAparicion.objects.get_or_create(
        personaje=personaje, unidad=solicitud.unidad,
        defaults={
            'origen': PropuestaAparicion.ORIGEN_MANUAL,
            'nota': f'Propuesto por {solicitud.usuario.username} al publicar.'[:300],
        },
    )
    aprobar_propuesta(propuesta)

    for fila in PersonajeComparado.objects.filter(solicitud=solicitud).select_related('post'):
        if PersonajeComparado.objects.filter(post_id=fila.post_id, personaje=personaje).exists():
            fila.delete()
        else:
            fila.personaje = personaje
            fila.save(update_fields=['personaje'])
        fila.post.personajes.add(personaje)

    solicitud.estado = SolicitudPersonaje.ESTADO_APROBADA
    solicitud.personaje = personaje
    solicitud.resuelto_en = timezone.now()
    solicitud.save(update_fields=['estado', 'personaje', 'resuelto_en'])
    return personaje


@transaction.atomic
def rechazar_solicitud_personaje(solicitud):
    """Retira el personaje propuesto de los posts que lo esperaban. False si no aplicaba."""
    from posts.models import PersonajeComparado

    if solicitud.estado != SolicitudPersonaje.ESTADO_PENDIENTE:
        return False

    PersonajeComparado.objects.filter(solicitud=solicitud, personaje__isnull=True).delete()
    solicitud.estado = SolicitudPersonaje.ESTADO_RECHAZADA
    solicitud.resuelto_en = timezone.now()
    solicitud.save(update_fields=['estado', 'resuelto_en'])
    return True