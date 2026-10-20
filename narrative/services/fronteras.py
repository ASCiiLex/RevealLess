"""Límites de la frontera de spoiler, compartidos por posts y comentarios."""

from django.utils import timezone

from ..models import UnidadNarrativa


def primera_hoja(unidad):
    """Primer episodio de una parte (la propia unidad si ya es hoja)."""
    return UnidadNarrativa.objects.filter(
        obra_id=unidad.obra_id, orden_inicio=unidad.orden_inicio, hijos__isnull=True,
    ).first()


def siguiente_hoja(unidad):
    """Primer episodio tras la unidad, o None si es lo último de la obra."""
    return UnidadNarrativa.objects.filter(
        obra_id=unidad.obra_id, orden_inicio=unidad.orden_fin + 1, hijos__isnull=True,
    ).first()


def previa_cerrada(unidad, hoy=None):
    """Un previo deja de valer como frontera al estrenarse su entrega: por su propia fecha
    o por la del episodio que lo sigue. Sin fechas sigue abierto (riesgo aceptado: el admin
    puede fijar la fecha de estreno en el propio previo)."""
    if unidad is None or not unidad.es_previa:
        return False
    hoy = hoy or timezone.localdate()
    if unidad.fecha and unidad.fecha <= hoy:
        return True
    siguiente = siguiente_hoja(unidad)
    return bool(siguiente and siguiente.fecha and siguiente.fecha <= hoy)


def frontera_sin_previa_cerrada(frontera):
    """Frontera calculada (IA, progreso o mínimo de la referencia) que cae en un previo ya
    cerrado: pasa a lo ya estrenado, que es más restrictivo."""
    if previa_cerrada(frontera):
        return siguiente_hoja(frontera) or frontera
    return frontera


def frontera_minima(frontera, referencia):
    """La parte es contexto, pero el contexto también informa: la frontera nunca queda por
    debajo del primer episodio de la parte de la que se habla (un previo, justo antes)."""
    if not (frontera and referencia):
        return frontera
    hoja = primera_hoja(referencia)
    if hoja and frontera.orden_frontera < hoja.orden_frontera:
        return hoja
    return frontera


def frontera_minima_temas(frontera, temas):
    """La etiqueta de un tema muestra su nombre: el post no se lee antes de la primera
    unidad de sus minihistorias (los temáticos sin unidades no exigen nada)."""
    for tema in temas:
        if not frontera or tema is None:
            continue
        primera = tema.unidades.order_by('orden_fin').first()
        if primera and frontera.orden_frontera < primera.orden_frontera:
            frontera = primera
    return frontera