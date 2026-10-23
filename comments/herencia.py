"""Comentarios que heredan la frontera de su post: qué hashtags aportan y qué pasa si el autor la rebaja."""

from narrative.models import ClasificacionNarrativa
from notifications.utils import extract_hashtags

HEREDADO = ClasificacionNarrativa.ORIGEN_HEREDADO_POST


def aporta_hashtags(comentario):
    """Solo el que hereda sin cruce propio: se ve exactamente con el post, nunca más allá."""
    return comentario.frontera_origen == HEREDADO and not comentario.obra_cruzada_id


def fronteras_de(post):
    """Fronteras del post antes de editarlo."""
    return {
        'frontera': post.frontera_spoiler,
        'orden': post.frontera_orden,
        'obra_cruzada_id': post.obra_cruzada_id,
        'cruzada': post.frontera_cruzada,
        'orden_cruzada': post.frontera_cruzada_orden,
    }


def se_rebaja(post, antes):
    """True si, tras editarlo, el post puede verse antes que con sus fronteras anteriores."""
    if (post.frontera_orden or 0) < (antes['orden'] or 0):
        return True
    if antes['cruzada'] is None:
        return False
    return (
        post.obra_cruzada_id != antes['obra_cruzada_id']
        or (post.frontera_cruzada_orden or 0) < antes['orden_cruzada']
    )


def congelar_heredados(post, antes):
    """Los comentarios ajenos se escribieron para las fronteras anteriores: las conservan como propias.
    Los del autor del post siguen su decisión. En «misma escena» el resultado es más estricto
    (exige las dos fronteras), nunca más permisivo."""
    if antes['frontera'] is None:
        return
    heredados = post.comments.filter(frontera_origen=HEREDADO).exclude(user_id=post.author_id)
    if antes['cruzada'] is not None:
        # Un comentario con cruce propio lo conserva.
        heredados.filter(obra_cruzada__isnull=True).update(
            obra_cruzada_id=antes['obra_cruzada_id'],
            frontera_cruzada=antes['cruzada'],
            frontera_cruzada_orden=antes['orden_cruzada'],
        )
    heredados.update(
        frontera_spoiler=antes['frontera'],
        frontera_orden=antes['orden'],
        frontera_origen=ClasificacionNarrativa.ORIGEN_EXPLICITO,
    )
    _retirar_hashtags_ajenos(post)


def _retirar_hashtags_ajenos(post):
    """El post conserva los hashtags de su texto y de los comentarios que aún los aportan."""
    nombres = set(extract_hashtags(post.text))
    textos = post.comments.filter(frontera_origen=HEREDADO, obra_cruzada__isnull=True).values_list('text', flat=True)
    for texto in textos:
        nombres.update(extract_hashtags(texto))
    post.post_hashtags.exclude(hashtag__name__in=nombres).delete()