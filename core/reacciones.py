from django.db.models import Count


def totales_agrupados(reacciones, campo, claves):
    """{id del objeto: {emoción: n}} con una sola consulta agrupada. Los objetos sin reacciones no aparecen."""
    totales = {}
    # order_by() vacío: el ordering del modelo rompería el GROUP BY.
    for fila in reacciones.order_by().values(campo, 'reaction').annotate(n=Count('id')):
        if fila['reaction'] in claves:
            totales.setdefault(fila[campo], dict.fromkeys(claves, 0))[fila['reaction']] = fila['n']
    return totales


def totales_de(totales, objeto_id, claves):
    return totales.get(objeto_id) or dict.fromkeys(claves, 0)