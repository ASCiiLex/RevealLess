"""Fusión de personajes duplicados en el que se conserva."""

from django.db import transaction
from django.utils import timezone

from ...models import EtapaPersonaje, Personaje, PropuestaAparicion, RelevanciaPersonaje


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