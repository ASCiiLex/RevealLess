"""Límites inferiores de la frontera de spoiler, compartidos por posts y comentarios."""

from ..models import UnidadNarrativa


def primera_hoja(unidad):
    """Primer episodio de una parte (la propia unidad si ya es hoja)."""
    return UnidadNarrativa.objects.filter(
        obra_id=unidad.obra_id, orden_inicio=unidad.orden_inicio, hijos__isnull=True,
    ).first()


def frontera_minima(frontera, referencia):
    """La parte es contexto, pero el contexto también informa: la frontera nunca queda por
    debajo del primer episodio de la parte de la que se habla (un previo, justo antes)."""
    if not (frontera and referencia):
        return frontera
    hoja = primera_hoja(referencia)
    if hoja and frontera.orden_frontera < hoja.orden_frontera:
        return hoja
    return frontera