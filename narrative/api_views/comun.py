from rest_framework.exceptions import ValidationError

from subscriptions.models import Suscripcion
from ..models import ProgresoUsuario, TemaTransversal


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
    ids_obras_suscritas = set()
    suscripcion_id_por_obra = {}
    filas = Suscripcion.objects.filter(usuario=user).values_list('id', 'obra_id', 'unidad_id', 'tema_id')
    for suscripcion_id, obra_id, unidad_id, tema_id in filas:
        ids_obras_suscritas.add(obra_id)
        if unidad_id is None and tema_id is None:
            suscripcion_id_por_obra[obra_id] = suscripcion_id
    return {
        'ids_obras_suscritas': ids_obras_suscritas,
        'suscripcion_id_por_obra': suscripcion_id_por_obra,
    }


def suscripcion_id_por_tema(user):
    return dict(
        Suscripcion.objects.filter(usuario=user, tema__isnull=False).values_list('tema_id', 'id')
    )


def temas_suscritos_serializados(user):
    """Temas a los que el usuario esta suscrito individualmente,
    listos para mostrarse como lomos en el carrusel de Biblioteca."""
    from ..serializers import TemaLomoSerializer

    ids_temas = set(suscripcion_id_por_tema(user).keys())
    if not ids_temas:
        return []

    temas = TemaTransversal.objects.filter(id__in=ids_temas).select_related('obra')
    contexto = {'suscripcion_id_por_tema': suscripcion_id_por_tema(user)}
    return TemaLomoSerializer(temas, many=True, context=contexto).data