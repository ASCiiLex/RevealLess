"""Personajes: revisión de apariciones, fusión de duplicados, orden del carrusel
y presentación según el progreso del lector."""

from collections import Counter
from datetime import date

from django.db import transaction
from django.utils import timezone

from ..models import EtapaPersonaje, Personaje, ProgresoUsuario, PropuestaAparicion, RelevanciaPersonaje

# Un post visible pesa como dos apariciones: refleja interés real, no solo presencia.
PESO_POSTS = 2


@transaction.atomic
def aprobar_propuesta(propuesta):
    propuesta.personaje.unidades.add(propuesta.unidad)
    propuesta.estado = PropuestaAparicion.ESTADO_APROBADA
    propuesta.resuelto_en = timezone.now()
    propuesta.save(update_fields=['estado', 'resuelto_en'])
    return propuesta


@transaction.atomic
def rechazar_propuesta(propuesta):
    # Rechazar una ya aprobada la retira de las landings.
    propuesta.personaje.unidades.remove(propuesta.unidad)
    propuesta.estado = PropuestaAparicion.ESTADO_RECHAZADA
    propuesta.resuelto_en = timezone.now()
    propuesta.save(update_fields=['estado', 'resuelto_en'])
    return propuesta


@transaction.atomic
def mover_aparicion(propuesta, unidad_anterior_id):
    """Si se corrige la unidad de una propuesta aprobada, la aparición se mueve con ella."""
    if propuesta.estado != PropuestaAparicion.ESTADO_APROBADA or unidad_anterior_id == propuesta.unidad_id:
        return propuesta
    propuesta.personaje.unidades.remove(unidad_anterior_id)
    propuesta.personaje.unidades.add(propuesta.unidad)
    return propuesta


def ordenar_por_relevancia(personajes, obra, usuario):
    """Orden del carrusel: relevancia editorial en la obra, después
    PESO_POSTS × posts visibles etiquetados + apariciones vistas, primera aparición y nombre.
    Solo cuentan posts etiquetados con el personaje (los anclados a una unidad hablan del
    episodio y sumarían a todos los que salen en él) y que el usuario puede ver: contar
    todos insinuaría quién gana peso más adelante. Espera las anotaciones de personajes_visibles."""
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

    def clave(p):
        peso = PESO_POSTS * posts[p.id] + p.apariciones_vistas
        return (-niveles.get(p.id, 0), -peso, p.primera_aparicion, p.nombre.lower())

    return sorted(personajes, key=clave)


def _fusionar_propuestas(origen, destino):
    for propuesta in list(origen.propuestas.all()):
        existente = destino.propuestas.filter(unidad_id=propuesta.unidad_id).first()
        if existente is None:
            propuesta.personaje = destino
            propuesta.save(update_fields=['personaje'])
            continue
        # Misma unidad en ambos: queda una; aprobada si alguna lo estaba.
        aprobada = PropuestaAparicion.ESTADO_APROBADA
        if propuesta.estado == aprobada and existente.estado != aprobada:
            existente.estado = aprobada
            existente.resuelto_en = propuesta.resuelto_en or timezone.now()
            existente.save(update_fields=['estado', 'resuelto_en'])
        propuesta.delete()


def _fusionar_etapas(origen, destino):
    for etapa in list(origen.etapas.all()):
        if destino.etapas.filter(visible_tras_id=etapa.visible_tras_id).exists():
            etapa.delete()
        else:
            etapa.personaje = destino
            etapa.save(update_fields=['personaje'])


def _fusionar_relevancias(origen, destino):
    # Misma obra en ambos: se conserva la mayor.
    for relevancia in list(origen.relevancias.all()):
        existente = destino.relevancias.filter(obra_id=relevancia.obra_id).first()
        if existente is None:
            relevancia.personaje = destino
            relevancia.save(update_fields=['personaje'])
            continue
        if relevancia.nivel > existente.nivel:
            existente.nivel = relevancia.nivel
            existente.save(update_fields=['nivel'])
        relevancia.delete()


def _fusionar_relaciones_externas(origen, destino):
    """Posts, suscripciones y cualquier otra relación hacia Personaje, sin importar otras apps."""
    propias = (PropuestaAparicion, EtapaPersonaje, RelevanciaPersonaje)
    for rel in Personaje._meta.related_objects:
        if rel.related_model in propias:
            continue
        if rel.many_to_many:
            accesor = rel.get_accessor_name()
            getattr(destino, accesor).add(*getattr(origen, accesor).all())
        elif rel.one_to_many:
            modelo, campo = rel.related_model, rel.field.name
            filas = modelo.objects.filter(**{campo: origen})
            if any(f.name == 'usuario' for f in modelo._meta.fields):
                # Una por usuario (suscripciones): se conserva la del destino.
                ya = modelo.objects.filter(**{campo: destino}).values_list('usuario_id', flat=True)
                filas.filter(usuario_id__in=list(ya)).delete()
            filas.update(**{campo: destino})


@transaction.atomic
def fusionar_personajes(origen, destino):
    """Une un duplicado en el personaje que se conserva y borra el duplicado."""
    if origen.pk == destino.pk:
        raise ValueError('No se puede fusionar un personaje consigo mismo.')

    _fusionar_propuestas(origen, destino)
    _fusionar_etapas(origen, destino)
    _fusionar_relevancias(origen, destino)
    destino.unidades.add(*origen.unidades.all())
    _fusionar_relaciones_externas(origen, destino)

    cambios = []
    if not destino.wikidata_id and origen.wikidata_id:
        wikidata_id = origen.wikidata_id
        origen.wikidata_id = None
        origen.save(update_fields=['wikidata_id'])
        destino.wikidata_id = wikidata_id
        cambios.append('wikidata_id')
    if not destino.imagen and origen.imagen:
        destino.imagen = origen.imagen.name
        cambios.append('imagen')
    if cambios:
        destino.save(update_fields=cambios)

    origen.delete()
    return destino


def progreso_por_obra(usuario):
    return dict(ProgresoUsuario.objects.filter(usuario=usuario).values_list('obra_id', 'orden_absoluto'))


def _superada(etapa, progreso):
    unidad = etapa.visible_tras
    alcanzado = progreso.get(unidad.obra_id)
    return alcanzado is not None and alcanzado >= unidad.orden_fin


def presentacion_personaje(personaje, progreso, obra_id=None):
    """Nombre, imagen y nota que puede ver el lector. Acumula las etapas cuya unidad
    ya terminó; cada campo vacío hereda el anterior. Con obra_id solo cuentan las
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

    datos = {'nombre': personaje.nombre, 'imagen_url': personaje.image_url, 'nota': None}
    for etapa in etapas:
        if etapa.alias:
            datos['nombre'] = etapa.alias
        if etapa.imagen:
            datos['imagen_url'] = etapa.imagen.url
        if etapa.nota:
            datos['nota'] = etapa.nota
    return datos