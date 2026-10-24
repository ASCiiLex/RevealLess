"""Longitud de una obra para el porcentaje de progreso: hasta la última hoja del tipo principal
(episodios en un anime, capítulos en un manga). Previos y películas intercaladas no cuentan,
igual que en la numeración del deslizador (frontend/src/utils/progresoPct.ts)."""

from collections import defaultdict

from django.db.models import Count, Exists, Max, OuterRef

from ..models import UnidadNarrativa


def longitudes_principales(obra_ids=None):
    """{obra_id: orden_fin de la última hoja del tipo principal}. Tipo principal: el más frecuente
    sin contar previos; en empate, el que llega más lejos. Con solo previos, la obra entera."""
    hojas = UnidadNarrativa.objects.filter(~Exists(UnidadNarrativa.objects.filter(padre=OuterRef('pk'))))
    if obra_ids is not None:
        hojas = hojas.filter(obra_id__in=obra_ids)
    filas = hojas.order_by().values('obra_id', 'tipo').annotate(total=Count('id'), fin=Max('orden_fin'))

    por_obra = defaultdict(list)
    for fila in filas:
        por_obra[fila['obra_id']].append(fila)

    longitudes = {}
    for obra_id, tipos in por_obra.items():
        sin_previos = [t for t in tipos if t['tipo'] != UnidadNarrativa.TIPO_PREVIO]
        if sin_previos:
            longitudes[obra_id] = max(sin_previos, key=lambda t: (t['total'], t['fin']))['fin']
        else:
            longitudes[obra_id] = max(t['fin'] for t in tipos)
    return longitudes