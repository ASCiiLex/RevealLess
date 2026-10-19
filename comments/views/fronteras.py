from narrative.models import ClasificacionNarrativa
from narrative.services.fronteras import frontera_minima, primera_hoja


def ajustar_frontera(comment):
    """Un comentario nunca se lee antes de la parte de la que habla.
    Propia: se eleva hasta el comienzo de su referencia. Heredada: se mantiene mientras la
    referencia no vaya más allá de la frontera del post; si va, pasa a propia en ese comienzo."""
    referencia = comment.referencia_narrativa
    if comment.frontera_origen != ClasificacionNarrativa.ORIGEN_HEREDADO_POST:
        comment.frontera_spoiler = frontera_minima(comment.frontera_spoiler, referencia)
        return

    hoja = primera_hoja(referencia) if referencia else None
    if hoja and hoja.orden_frontera > (comment.post.frontera_orden or 0):
        # Derivada de la referencia que eligió el autor: cuenta como explícita.
        comment.frontera_spoiler = hoja
        comment.frontera_origen = ClasificacionNarrativa.ORIGEN_EXPLICITO