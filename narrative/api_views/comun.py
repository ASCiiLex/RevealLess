from django.db.models import Min
from rest_framework.exceptions import ValidationError

from subscriptions.models import Suscripcion
from ..models import Personaje, ProgresoUsuario, TemaTransversal, UnidadNarrativa
from ..services.personajes import progreso_por_obra


def entero_o_none(valor, campo):
    """None si no viene; int si es válido; 400 si no es numérico."""
    if valor in (None, ''):
        return None
    if not str(valor).isdigit():
        raise ValidationError({campo: ['Debe ser un número entero.']})
    return int(valor)


def es_verdadero(valor):
    # bool('false') es True: se interpreta el texto explícitamente.
    return str(valor).strip().lower() in ('true', '1', 'on')


def ids_familia(obra):
    """La obra y sus relacionadas (adaptaciones, hermanas y mismo universo)."""
    return [obra.id] + list(obra.obras_relacionadas().values_list('id', flat=True))


def ids_biblioteca(user):
    """Obras con progreso declarado o alguna suscripción (silenciadas incluidas)."""
    con_progreso = ProgresoUsuario.objects.filter(usuario=user).values_list('obra_id', flat=True)
    suscritas = Suscripcion.objects.filter(usuario=user, obra__isnull=False).values_list('obra_id', flat=True)
    return set(con_progreso) | set(suscritas)


def obra_basica(obra):
    return {'id': obra.id, 'titulo': obra.titulo, 'slug': obra.slug}


def temas_planos(obra):
    return [
        {'id': t.id, 'nombre': t.nombre}
        for t in TemaTransversal.objects.filter(obra=obra).order_by('nombre')
    ]


def contexto_suscripcion_obra(user):
    """Estado de la suscripción a la obra completa: la única que el lomo sigue o deja de seguir.
    Las de tema, unidad o personaje no marcan la obra como seguida."""
    suscripcion_id_por_obra = {}
    ids_obras_silenciadas = set()
    filas = Suscripcion.objects.filter(
        usuario=user, obra__isnull=False, unidad__isnull=True, tema__isnull=True,
    ).values_list('id', 'obra_id', 'activa')
    for suscripcion_id, obra_id, activa in filas:
        suscripcion_id_por_obra[obra_id] = suscripcion_id
        if not activa:
            ids_obras_silenciadas.add(obra_id)
    return {
        'ids_obras_suscritas': set(suscripcion_id_por_obra),
        'suscripcion_id_por_obra': suscripcion_id_por_obra,
        'ids_obras_silenciadas': ids_obras_silenciadas,
    }


def suscripcion_id_por_tema(user):
    return dict(
        Suscripcion.objects.filter(usuario=user, tema__isnull=False).values_list('tema_id', 'id')
    )


def temas_suscritos_serializados(user):
    """Temas a los que el usuario está suscrito individualmente,
    listos para mostrarse como lomos en el carrusel de Biblioteca."""
    from ..serializers import TemaLomoSerializer

    filas = list(
        Suscripcion.objects.filter(usuario=user, tema__isnull=False).values_list('tema_id', 'id', 'activa')
    )
    if not filas:
        return []

    contexto = {
        'suscripcion_id_por_tema': {tema_id: suscripcion_id for tema_id, suscripcion_id, _ in filas},
        'ids_temas_silenciados': {tema_id for tema_id, _, activa in filas if not activa},
    }
    temas = TemaTransversal.objects.filter(id__in=contexto['suscripcion_id_por_tema']).select_related('obra')
    return TemaLomoSerializer(temas, many=True, context=contexto).data


def personajes_suscritos_serializados(user):
    """Personajes suscritos como lomos de Biblioteca. Solo los ya alcanzados en alguna obra:
    sin ninguna aparición alcanzada (p. ej., tras retroceder) se ocultan, igual que su landing."""
    from ..serializers import PersonajeLomoSerializer

    filas = list(
        Suscripcion.objects.filter(usuario=user, personaje__isnull=False)
        .values_list('personaje_id', 'id', 'activa')
    )
    if not filas:
        return []

    progreso = progreso_por_obra(user)
    primeras = (
        UnidadNarrativa.objects
        .filter(personajes__in=[personaje_id for personaje_id, _, _ in filas])
        .order_by()
        .values('personajes', 'obra_id')
        .annotate(primera=Min('orden_fin'))
    )
    alcanzados = {f['personajes'] for f in primeras if progreso.get(f['obra_id'], -1) >= f['primera']}
    if not alcanzados:
        return []

    contexto = {
        'progreso_por_obra': progreso,
        'suscripcion_id_por_personaje': {p: s for p, s, _ in filas},
        'ids_personajes_silenciados': {p for p, _, activa in filas if not activa},
    }
    personajes = Personaje.objects.filter(id__in=alcanzados).prefetch_related('etapas__visible_tras')
    return PersonajeLomoSerializer(personajes, many=True, context=contexto).data