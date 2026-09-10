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


def _posts_de_suscripcion(suscripcion):
    """Resuelve qué posts pertenecen a una suscripción, sin aplicar
    todavía visible_for() — eso lo hace siempre la capa que consuma esto
    (feed, contador de no leídos), nunca aquí, para que sea imposible
    usar esta función como vía lateral que se salte el motor anti-spoiler."""
    from posts.models import Post  # import diferido: evita dependencia de carga entre apps

    qs = Post.objects.filter(obra=suscripcion.obra)

    if suscripcion.unidad_id:
        # "sigue este nodo" incluye todo lo que cuelga por debajo en el
        # árbol: mismo criterio de rango que ya usa recalcular_orden().
        qs = qs.filter(
            referencia_narrativa__orden_inicio__gte=suscripcion.unidad.orden_inicio,
            referencia_narrativa__orden_fin__lte=suscripcion.unidad.orden_fin,
        )
    elif suscripcion.tema_id:
        qs = qs.filter(temas_transversales=suscripcion.tema)

    return qs.distinct()


def posts_no_leidos_count(suscripcion):
    posts = _posts_de_suscripcion(suscripcion)
    if suscripcion.ultima_visita:
        posts = posts.filter(created_at__gt=suscripcion.ultima_visita)
    else:
        posts = posts.filter(created_at__gte=suscripcion.creado_en)
    return posts.count()