"""Identidades vinculadas (Sogeking → Usopp, Tobi → Obito): visibles solo cuando el lector conoce el vínculo."""

from django.db.models import Min

from ...models import Personaje
from .presentacion import progreso_por_obra


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