"""Personajes: revisión de apariciones, solicitudes de usuarios, identidades vinculadas,
fusión de duplicados, orden del carrusel y presentación según el progreso del lector."""

from collections import Counter
from datetime import date

from django.db import transaction
from django.db.models import Min
from django.utils import timezone

from ..models import (
    EtapaPersonaje,
    Personaje,
    ProgresoUsuario,
    PropuestaAparicion,
    RelevanciaPersonaje,
    SolicitudPersonaje,
)

# Un post visible pesa como dos apariciones: refleja interés real, no solo presencia.
PESO_POSTS = 2
# Desde este nivel el carrusel sigue el orden de presentación: el reparto principal
# no debe bailar por lo desigual que sea el registro de apariciones.
NIVEL_ORDEN_DE_PRESENTACION = RelevanciaPersonaje.NIVEL_PRINCIPAL


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
def aplicar_cambio_propuesta(propuesta, estado_anterior=None, unidad_anterior_id=None):
    """Sincroniza Personaje.unidades tras editar estado o unidad a mano (ya guardada).
    estado_anterior/unidad_anterior_id: valores en BD antes de guardar; None si es nueva."""
    if propuesta.estado == estado_anterior and propuesta.unidad_id == unidad_anterior_id:
        return propuesta
    if estado_anterior == PropuestaAparicion.ESTADO_APROBADA and unidad_anterior_id is not None:
        propuesta.personaje.unidades.remove(unidad_anterior_id)
    if propuesta.estado == PropuestaAparicion.ESTADO_APROBADA:
        return aprobar_propuesta(propuesta)
    if propuesta.estado == PropuestaAparicion.ESTADO_RECHAZADA:
        return rechazar_propuesta(propuesta)
    # Vuelta a pendiente.
    if propuesta.resuelto_en is not None:
        propuesta.resuelto_en = None
        propuesta.save(update_fields=['resuelto_en'])
    return propuesta


@transaction.atomic
def eliminar_propuesta(propuesta):
    if propuesta.estado == PropuestaAparicion.ESTADO_APROBADA:
        propuesta.personaje.unidades.remove(propuesta.unidad_id)
    propuesta.delete()


def proponer_personaje(obra, unidad, usuario, nombre):
    """Personaje propuesto al publicar. Reutiliza la solicitud pendiente con el mismo
    nombre en la obra: varios posts pueden esperar al mismo personaje."""
    nombre = ' '.join(nombre.split())[:150]
    pendiente = SolicitudPersonaje.objects.filter(
        obra=obra, nombre__iexact=nombre, estado=SolicitudPersonaje.ESTADO_PENDIENTE,
    ).first()
    if pendiente:
        return pendiente
    return SolicitudPersonaje.objects.create(obra=obra, unidad=unidad, usuario=usuario, nombre=nombre)


@transaction.atomic
def aprobar_solicitud_personaje(solicitud):
    """Crea o reutiliza el personaje (el elegido en la solicitud, o el que coincida por nombre),
    aprueba su aparición en la unidad de la solicitud y lo vincula a los posts que lo propusieron.
    Devuelve el personaje, o None si la solicitud no estaba pendiente."""
    from posts.models import PersonajeComparado  # import diferido: posts depende de narrative

    if solicitud.estado != SolicitudPersonaje.ESTADO_PENDIENTE:
        return None

    personaje = (
        solicitud.personaje
        or Personaje.objects.filter(nombre__iexact=solicitud.nombre).first()
        or Personaje.objects.create(nombre=solicitud.nombre)
    )
    propuesta, _ = PropuestaAparicion.objects.get_or_create(
        personaje=personaje, unidad=solicitud.unidad,
        defaults={
            'origen': PropuestaAparicion.ORIGEN_MANUAL,
            'nota': f'Propuesto por {solicitud.usuario.username} al publicar.'[:300],
        },
    )
    aprobar_propuesta(propuesta)

    for fila in PersonajeComparado.objects.filter(solicitud=solicitud).select_related('post'):
        if PersonajeComparado.objects.filter(post_id=fila.post_id, personaje=personaje).exists():
            fila.delete()
        else:
            fila.personaje = personaje
            fila.save(update_fields=['personaje'])
        fila.post.personajes.add(personaje)

    solicitud.estado = SolicitudPersonaje.ESTADO_APROBADA
    solicitud.personaje = personaje
    solicitud.resuelto_en = timezone.now()
    solicitud.save(update_fields=['estado', 'personaje', 'resuelto_en'])
    return personaje


@transaction.atomic
def rechazar_solicitud_personaje(solicitud):
    """Retira el personaje propuesto de los posts que lo esperaban. False si no aplicaba."""
    from posts.models import PersonajeComparado

    if solicitud.estado != SolicitudPersonaje.ESTADO_PENDIENTE:
        return False

    PersonajeComparado.objects.filter(solicitud=solicitud, personaje__isnull=True).delete()
    solicitud.estado = SolicitudPersonaje.ESTADO_RECHAZADA
    solicitud.resuelto_en = timezone.now()
    solicitud.save(update_fields=['estado', 'resuelto_en'])
    return True


def identidad_conocida(alter, progreso):
    """¿Sabe ya el lector que 'alter' es otra identidad de alter.identidad_de?
    Con unidades de revelación, al superar cualquiera; sin ellas, desde la primera
    aparición alcanzada del alter ego (disfraz evidente, como Sogeking)."""
    if not alter.identidad_de_id:
        return False
    reveladoras = list(alter.identidad_revelada_tras.all())
    if reveladoras:
        return any(progreso.get(u.obra_id, -1) >= u.orden_fin for u in reveladoras)
    primeras = alter.unidades.order_by().values('obra_id').annotate(primera=Min('orden_fin'))
    return any(progreso.get(f['obra_id'], -1) >= f['primera'] for f in primeras)


def identidades_conocidas(personaje, progreso):
    """Otras identidades del personaje cuyo vínculo ya conoce el lector."""
    alters = personaje.otras_identidades.prefetch_related('identidad_revelada_tras', 'etapas__visible_tras')
    return [a for a in alters if identidad_conocida(a, progreso)]


def ids_con_identidades(personaje_id, usuario):
    """El personaje y sus otras identidades ya conocidas: feed y suscripción de Usopp incluyen a Sogeking."""
    alters = Personaje.objects.filter(identidad_de_id=personaje_id).prefetch_related('identidad_revelada_tras')
    if not alters:
        return [personaje_id]
    progreso = progreso_por_obra(usuario)
    return [personaje_id] + [a.id for a in alters if identidad_conocida(a, progreso)]


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