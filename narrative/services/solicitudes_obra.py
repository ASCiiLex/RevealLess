"""Sugerencias de obras para el catálogo: proponer, aprobar y rechazar."""

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from ..models import Obra, SolicitudObra
from . import asegurar_unidad_previa

MAX_PENDIENTES_POR_USUARIO = 10
# SlugField admite 50: se deja sitio para el sufijo de desambiguación.
LONGITUD_BASE_SLUG = 45


class SolicitudNoValida(Exception):
    pass


def _titulo_limpio(titulo):
    return ' '.join(str(titulo or '').split())[:200]


def proponer_obra(usuario, titulo, tipo=Obra.TIPO_SERIE, enlace='', comentario=''):
    titulo = _titulo_limpio(titulo)
    if not titulo:
        raise SolicitudNoValida('Indica el título de la obra.')

    existente = Obra.objects.filter(Q(titulo__iexact=titulo) | Q(slug=slugify(titulo))).first()
    if existente:
        raise SolicitudNoValida(f'«{existente.titulo}» ya está en el catálogo: búscala y síguela.')

    pendientes = SolicitudObra.objects.filter(usuario=usuario, estado=SolicitudObra.ESTADO_PENDIENTE)
    if pendientes.filter(titulo__iexact=titulo).exists():
        raise SolicitudNoValida('Ya sugeriste esta obra: está pendiente de revisión.')
    if pendientes.count() >= MAX_PENDIENTES_POR_USUARIO:
        raise SolicitudNoValida(
            f'Tienes {MAX_PENDIENTES_POR_USUARIO} sugerencias pendientes: espera a que se revisen.'
        )

    return SolicitudObra.objects.create(
        usuario=usuario, titulo=titulo, tipo=tipo, enlace=enlace, comentario=comentario[:300],
    )


def _slug_libre(titulo):
    base = slugify(titulo)[:LONGITUD_BASE_SLUG] or 'obra'
    slug, sufijo = base, 2
    while Obra.objects.filter(slug=slug).exists():
        slug = f'{base}-{sufijo}'
        sufijo += 1
    return slug


def _pendientes_iguales(solicitud):
    return SolicitudObra.objects.filter(
        estado=SolicitudObra.ESTADO_PENDIENTE, titulo__iexact=solicitud.titulo,
    ).select_related('usuario')


def _notificar(solicitudes, admin, texto, obra=None):
    """Sin admin (scripts, tests de lógica) no hay actor para la notificación: no se envía."""
    if admin is None:
        return
    from notifications.models import Notification
    from notifications.utils import send_ws_notification

    for solicitud in solicitudes:
        notificacion = Notification.objects.create(
            user=solicitud.usuario, actor=admin, verb=texto(solicitud),
            target_type='obra', target_id=obra.id if obra else None,
        )
        send_ws_notification(solicitud.usuario, notificacion)


def aprobar_solicitud_obra(solicitud, admin=None):
    """Crea la obra (o usa la vinculada por el admin) con su previo y resuelve todas las sugerencias
    pendientes del mismo título. Devuelve la obra, o None si la solicitud ya estaba resuelta."""
    if solicitud.estado != SolicitudObra.ESTADO_PENDIENTE:
        return None

    with transaction.atomic():
        obra = solicitud.obra or Obra.objects.create(
            titulo=solicitud.titulo, slug=_slug_libre(solicitud.titulo), tipo=solicitud.tipo,
        )
        resueltas = list(_pendientes_iguales(solicitud))
        SolicitudObra.objects.filter(id__in=[s.id for s in resueltas]).update(
            estado=SolicitudObra.ESTADO_APROBADA, obra=obra, resuelto_en=timezone.now(),
        )

    # Sin estructura todavía: el previo permite declarar progreso y publicar desde ya.
    asegurar_unidad_previa(obra)
    _notificar(resueltas, admin, lambda s: f'añadió «{obra.titulo}» al catálogo, la obra que sugeriste', obra)
    return obra


def rechazar_solicitud_obra(solicitud, admin=None):
    """Resuelve como rechazadas todas las pendientes del mismo título. False si ya estaba resuelta."""
    if solicitud.estado != SolicitudObra.ESTADO_PENDIENTE:
        return False

    resueltas = list(_pendientes_iguales(solicitud))
    SolicitudObra.objects.filter(id__in=[s.id for s in resueltas]).update(
        estado=SolicitudObra.ESTADO_RECHAZADA, resuelto_en=timezone.now(),
    )
    _notificar(resueltas, admin, lambda s: f'revisó tu sugerencia «{s.titulo}»: por ahora no se añadirá al catálogo')
    return True