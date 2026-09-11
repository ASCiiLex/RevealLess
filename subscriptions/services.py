from django.db.models import Q
from django.utils import timezone

from .models import Suscripcion


def crear_suscripcion(usuario, obra, unidad=None, tema=None):
    """Idempotente: si ya existe la misma suscripción exacta, la devuelve
    en vez de duplicarla. unique_together no es fiable aquí porque NULL
    no es comparable a NULL en SQL (varias filas con unidad=NULL y
    tema=NULL no violarían una constraint de unicidad), así que la
    deduplicación se resuelve aquí, en Python."""
    if unidad is not None and tema is not None:
        raise ValueError('Una suscripción no puede fijar unidad y tema a la vez.')

    existente = Suscripcion.objects.filter(
        usuario=usuario, obra=obra, unidad=unidad, tema=tema,
    ).first()
    if existente:
        return existente

    suscripcion = Suscripcion(usuario=usuario, obra=obra, unidad=unidad, tema=tema)
    suscripcion.full_clean()
    suscripcion.save()
    return suscripcion


def eliminar_suscripcion(usuario, obra, unidad=None, tema=None):
    Suscripcion.objects.filter(
        usuario=usuario, obra=obra, unidad=unidad, tema=tema,
    ).delete()


def marcar_visto(suscripcion):
    suscripcion.ultima_visita = timezone.now()
    suscripcion.save(update_fields=['ultima_visita'])


def silenciar_suscripcion(suscripcion):
    suscripcion.activa = False
    suscripcion.save(update_fields=['activa'])


def reactivar_suscripcion(suscripcion):
    suscripcion.activa = True
    suscripcion.save(update_fields=['activa'])


def _posts_de_suscripcion(suscripcion):
    """Resuelve qué posts pertenecen a una suscripción, sin aplicar
    todavía visible_for() — eso lo hace siempre la capa que consuma esto
    (feed, contador de no leídos), nunca aquí, para que sea imposible
    usar una suscripción como vía lateral que se salte el motor
    anti-spoiler."""
    from posts.models import Post  # import diferido: evita dependencia de carga entre apps

    qs = Post.objects.filter(obra=suscripcion.obra)

    if suscripcion.unidad_id:
        qs = qs.filter(
            referencia_narrativa__orden_inicio__gte=suscripcion.unidad.orden_inicio,
            referencia_narrativa__orden_fin__lte=suscripcion.unidad.orden_fin,
        )
    elif suscripcion.tema_id:
        qs = qs.filter(temas_transversales=suscripcion.tema_id)

    return qs.distinct()


def posts_no_leidos_count(suscripcion):
    """El contador de no leídos NUNCA debe filtrar solo por pertenencia
    a la suscripción — eso sería una fuga de información: el número
    insinuaría contenido futuro que el usuario aún no puede ver según su
    progreso, aunque el propio post permanezca oculto. Todo post debe
    pasar primero por visible_for(usuario), exactamente igual que en el
    feed. 'Estoy suscrito' decide qué podría interesarme; 'puedo verlo'
    decide qué cuenta como pendiente de leer."""
    if not suscripcion.activa:
        return 0

    posts = _posts_de_suscripcion(suscripcion).visible_for(suscripcion.usuario)
    if suscripcion.ultima_visita:
        posts = posts.filter(created_at__gt=suscripcion.ultima_visita)
    else:
        posts = posts.filter(created_at__gte=suscripcion.creado_en)
    return posts.count()


def filtro_posts_suscripciones(usuario):
    """Construye un único Q() que representa TODOS los posts
    potencialmente accesibles por las suscripciones ACTIVAS del usuario,
    en una sola pasada. Las suscripciones silenciadas no aportan aquí —
    su exclusión se resuelve aparte, en filtro_posts_silenciados()."""
    suscripciones = Suscripcion.objects.filter(usuario=usuario, activa=True).select_related(
        'obra', 'unidad', 'tema'
    )

    query = Q(pk__in=[])
    for suscripcion in suscripciones:
        if suscripcion.unidad_id:
            query |= Q(
                obra_id=suscripcion.obra_id,
                referencia_narrativa__orden_inicio__gte=suscripcion.unidad.orden_inicio,
                referencia_narrativa__orden_fin__lte=suscripcion.unidad.orden_fin,
            )
        elif suscripcion.tema_id:
            query |= Q(obra_id=suscripcion.obra_id, temas_transversales=suscripcion.tema_id)
        else:
            query |= Q(obra_id=suscripcion.obra_id)

    return query


def filtro_posts_silenciados(usuario):
    """Q() del alcance de todas las suscripciones SILENCIADAS
    (activa=False) del usuario. El feed debe excluir (.exclude()) los
    posts que caigan aquí, de forma incondicional: el silencio prevalece
    aunque el mismo post llegue por otra vía (seguido, suscripción
    activa, o incluso autoría propia — silenciar un tema propio también
    lo oculta de tu propio feed, por diseño: 'silenciar' significa dejar
    de verlo, sin excepciones)."""
    suscripciones = Suscripcion.objects.filter(usuario=usuario, activa=False).select_related(
        'obra', 'unidad', 'tema'
    )

    query = Q(pk__in=[])
    for suscripcion in suscripciones:
        if suscripcion.unidad_id:
            query |= Q(
                obra_id=suscripcion.obra_id,
                referencia_narrativa__orden_inicio__gte=suscripcion.unidad.orden_inicio,
                referencia_narrativa__orden_fin__lte=suscripcion.unidad.orden_fin,
            )
        elif suscripcion.tema_id:
            query |= Q(obra_id=suscripcion.obra_id, temas_transversales=suscripcion.tema_id)
        else:
            query |= Q(obra_id=suscripcion.obra_id)

    return query