"""Lo que el lector puede ver de un personaje según su progreso: nombre, imagen,
nota, nombres buscables, nivel de relevancia y orden del carrusel."""

from collections import Counter
from datetime import date

from core.imagenes.miniaturas import url_miniatura

from ...models import ProgresoUsuario, RelevanciaPersonaje

# Un post visible pesa como dos apariciones: refleja interés real, no solo presencia.
PESO_POSTS = 2
# Desde este nivel el carrusel sigue el orden de presentación: el reparto principal
# no debe bailar por lo desigual que sea el registro de apariciones.
NIVEL_ORDEN_DE_PRESENTACION = RelevanciaPersonaje.NIVEL_PRINCIPAL


def progreso_por_obra(usuario):
    return dict(ProgresoUsuario.objects.filter(usuario=usuario).values_list('obra_id', 'orden_absoluto'))


def _superada(etapa, progreso):
    unidad = etapa.visible_tras
    alcanzado = progreso.get(unidad.obra_id)
    return alcanzado is not None and alcanzado >= unidad.orden_fin


def presentacion_personaje(personaje, progreso, obra_id=None):
    """Nombre, imagen (miniatura) y nota que puede ver el lector. Acumula las etapas cuya
    unidad ya terminó; cada campo vacío hereda el anterior. Con obra_id solo cuentan las
    etapas de esa obra; sin él, todas, por fecha de su unidad.
    Conviene prefetch_related('etapas__visible_tras')."""
    etapas = [
        e for e in personaje.etapas.all()
        if _superada(e, progreso) and (obra_id is None or e.visible_tras.obra_id == obra_id)
    ]
    if obra_id is None:
        etapas.sort(key=lambda e: (e.visible_tras.fecha or date.min, e.visible_tras.orden_fin))
    else:
        etapas.sort(key=lambda e: e.visible_tras.orden_fin)

    datos = {'nombre': personaje.nombre, 'imagen_url': personaje.miniatura_url, 'nota': None}
    for etapa in etapas:
        if etapa.alias:
            datos['nombre'] = etapa.alias
        if etapa.imagen:
            datos['imagen_url'] = url_miniatura(etapa.imagen) or datos['imagen_url']
        if etapa.nota:
            datos['nota'] = etapa.nota
    return datos


def nombres_conocidos(personaje, obra_id, hasta_orden, primera_aparicion):
    """Nombres que el lector ya ha visto del personaje en esta obra: los alias de etapas
    superadas y el nombre base solo si llegó a mostrarse antes del primer alias
    (con «Nico Robin» de base y «Miss All Sunday» desde su aparición, el base aún no se vio)."""
    con_alias = sorted(
        (e for e in personaje.etapas.all() if e.alias and e.visible_tras.obra_id == obra_id),
        key=lambda e: e.visible_tras.orden_fin,
    )
    nombres = {e.alias for e in con_alias if e.visible_tras.orden_fin <= hasta_orden}
    if not con_alias or primera_aparicion < con_alias[0].visible_tras.orden_fin:
        nombres.add(personaje.nombre)
    return nombres


def _nivel_con_etapas(personaje, obra_id, nivel_base, progreso):
    """Nivel de la última etapa superada de esta obra que lo fije; si ninguna, el base."""
    etapas = [
        e for e in personaje.etapas.all()
        if e.nivel and e.visible_tras.obra_id == obra_id and _superada(e, progreso)
    ]
    if not etapas:
        return nivel_base
    return max(etapas, key=lambda e: e.visible_tras.orden_fin).nivel


def ordenar_por_relevancia(personajes, obra, usuario):
    """Orden del carrusel. Primero el nivel en la obra según el progreso (etapa superada con
    nivel > relevancia de la obra > Secundario). Protagonistas y principales van por orden de
    presentación; el resto, por PESO_POSTS × posts visibles etiquetados + apariciones vistas.
    Solo cuentan posts etiquetados con el personaje y visibles para el usuario: contar todos
    insinuaría quién gana peso más adelante. Espera las anotaciones y el prefetch de
    personajes_visibles. Deja el nivel en p.nivel_relevancia para los chips."""
    from posts.models import Post  # import diferido: posts depende de narrative

    ids = [p.id for p in personajes]
    if not ids:
        return personajes

    visibles = Post.objects.filter(obra=obra).visible_for(usuario).values('pk')
    posts = Counter(
        Post.personajes.through.objects.filter(post_id__in=visibles, personaje_id__in=ids)
        .values_list('personaje_id', flat=True)
    )
    niveles = dict(
        RelevanciaPersonaje.objects.filter(obra=obra, personaje_id__in=ids).values_list('personaje_id', 'nivel')
    )
    progreso = progreso_por_obra(usuario)
    for p in personajes:
        base = niveles.get(p.id, RelevanciaPersonaje.NIVEL_SIN_MARCAR)
        p.nivel_relevancia = _nivel_con_etapas(p, obra.id, base, progreso)

    def clave(p):
        if p.nivel_relevancia >= NIVEL_ORDEN_DE_PRESENTACION:
            return (-p.nivel_relevancia, 0, p.primera_aparicion, p.nombre.lower())
        peso = PESO_POSTS * posts[p.id] + p.apariciones_vistas
        return (-p.nivel_relevancia, -peso, p.primera_aparicion, p.nombre.lower())

    return sorted(personajes, key=clave)