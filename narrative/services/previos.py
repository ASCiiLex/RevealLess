"""Previos al estreno de entregas anunciadas (temporadas, películas, arcos)."""

from ..models import UnidadNarrativa
from .fronteras import primera_hoja


def crear_previo(unidad):
    """Previo justo antes de 'unidad': hermano con su mismo orden_local, que el orden coloca
    delante. Así su frontera es el final de la entrega anterior. Idempotente.
    Hereda la fecha de estreno de la unidad o de su primer episodio, si la tienen."""
    if unidad.es_previa:
        return unidad

    existente = UnidadNarrativa.objects.filter(
        obra_id=unidad.obra_id, padre_id=unidad.padre_id, orden_local=unidad.orden_local,
        tipo=UnidadNarrativa.TIPO_PREVIO,
    ).first()
    if existente:
        return existente

    hoja = primera_hoja(unidad)
    previo = UnidadNarrativa.objects.create(
        obra=unidad.obra,
        padre=unidad.padre,
        tipo=UnidadNarrativa.TIPO_PREVIO,
        nombre=f'Previo · {unidad.nombre}',
        orden_local=unidad.orden_local,
        fecha=unidad.fecha or (hoja.fecha if hoja else None),
        traducido=True,
    )
    unidad.obra.recalcular_orden()
    previo.refresh_from_db()
    return previo