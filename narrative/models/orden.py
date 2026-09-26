"""Cálculo de orden_inicio/orden_fin (DFS) sobre el árbol de UnidadNarrativa.
Sin imports de modelos: opera vía obra.unidades para evitar ciclos."""


def recalcular_orden(obra):
    """orden_manual es un índice de inserción (1-based) sobre la secuencia
    final de hojas, no un valor absoluto: el resto se renumera sin huecos
    ni colisiones. Empates en el mismo índice se resuelven por orden DFS."""
    unidades = list(obra.unidades.all())
    por_padre = _agrupar_por_padre(unidades)

    hojas_dfs = _hojas_en_dfs(por_padre)
    secuencia = _aplicar_orden_manual(hojas_dfs)
    posiciones = {u.id: i + 1 for i, u in enumerate(secuencia)}
    rangos = _calcular_rangos(por_padre, posiciones)

    for unidad in unidades:
        ini, fin = rangos.get(unidad.id, (unidad.orden_inicio, unidad.orden_fin))
        if unidad.orden_inicio != ini or unidad.orden_fin != fin:
            obra.unidades.filter(pk=unidad.pk).update(orden_inicio=ini, orden_fin=fin)


def _agrupar_por_padre(unidades):
    por_padre = {}
    for u in unidades:
        por_padre.setdefault(u.padre_id, []).append(u)
    for hijos in por_padre.values():
        hijos.sort(key=lambda u: u.orden_local)
    return por_padre


def _hojas_en_dfs(por_padre):
    hojas = []

    def recorrer(unidad):
        hijos = por_padre.get(unidad.id, [])
        if not hijos:
            hojas.append(unidad)
            return
        for hijo in hijos:
            recorrer(hijo)

    for raiz in por_padre.get(None, []):
        recorrer(raiz)
    return hojas


def _aplicar_orden_manual(hojas_dfs):
    indice_dfs = {u.id: i for i, u in enumerate(hojas_dfs)}
    manuales = sorted(
        (u for u in hojas_dfs if u.orden_manual is not None),
        key=lambda u: (u.orden_manual, indice_dfs[u.id]),
    )
    secuencia = [u for u in hojas_dfs if u.orden_manual is None]

    usados = {}
    for unidad in manuales:
        desplazamiento = usados.get(unidad.orden_manual, 0)
        usados[unidad.orden_manual] = desplazamiento + 1
        indice = min(max(unidad.orden_manual + desplazamiento, 1), len(secuencia) + 1)
        secuencia.insert(indice - 1, unidad)
    return secuencia


def _calcular_rangos(por_padre, posiciones):
    rangos = {}

    def calcular(unidad):
        hijos = por_padre.get(unidad.id, [])
        if not hijos:
            pos = posiciones[unidad.id]
            rangos[unidad.id] = (pos, pos)
            return rangos[unidad.id]
        extremos = [calcular(hijo) for hijo in hijos]
        rangos[unidad.id] = (min(e[0] for e in extremos), max(e[1] for e in extremos))
        return rangos[unidad.id]

    for raiz in por_padre.get(None, []):
        calcular(raiz)
    return rangos