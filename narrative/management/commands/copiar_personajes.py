import re
import unicodedata
from collections import Counter

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from narrative.models import EtapaPersonaje, Obra, PropuestaAparicion, RelevanciaPersonaje, UnidadNarrativa
from narrative.services.personajes import aprobar_propuesta

# Unidades sueltas: se suben a su agrupación (arco, libro, película) para emparejar entre obras.
HOJAS = {'episodio', 'capitulo', 'capítulo', 'corto'}
PALABRAS_VACIAS = {'arco', 'de', 'del', 'la', 'las', 'el', 'los', 'y', 'a', 'isla', 'island'}


def _tokens(nombre):
    texto = unicodedata.normalize('NFKD', nombre)
    texto = ''.join(c for c in texto if not unicodedata.combining(c)).lower()
    texto = re.sub(r'\((parte \d+|continuacion)\)|-\s*parte \d+', ' ', texto)
    return frozenset(w for w in re.findall(r'\w+', texto) if w not in PALABRAS_VACIAS)


def claves_origen(nombre):
    """«Arco del País de Wano (parte 2)» ≈ «Arco del País de Wano»; «El Hobbit: Un viaje…» ≈ «El Hobbit»."""
    claves = [_tokens(nombre)]
    if ':' in nombre:
        claves.append(_tokens(nombre.split(':')[0]))
    return [c for c in claves if c]


class Command(BaseCommand):
    help = ('Copia a otra obra (adaptación) las apariciones aprobadas, las relevancias y, con --etapas, las '
            'etapas con su imagen, emparejando arcos, libros o películas por nombre. No sobrescribe nada.')

    def add_arguments(self, parser):
        parser.add_argument('--desde', required=True, help='Slug de la obra con los datos.')
        parser.add_argument('--hasta', required=True, help='Slug de la obra que los recibe.')
        parser.add_argument('--etapas', action='store_true', help='Copia también etapas (alias, nota, nivel, imagen).')
        parser.add_argument('--dry-run', action='store_true', help='Ejecuta todo y lo deshace al final.')

    def handle(self, *args, **opciones):
        desde, hasta = self._obra(opciones['desde']), self._obra(opciones['hasta'])
        self.indice = {}
        for unidad in UnidadNarrativa.objects.filter(obra=hasta).exclude(tipo__in=HOJAS).order_by('orden_fin'):
            self.indice.setdefault(_tokens(unidad.nombre), []).append(unidad)
        self.sin_par = Counter()

        with transaction.atomic():
            apariciones = self._apariciones(desde)
            relevancias = self._relevancias(desde, hasta)
            etapas, imagenes = self._etapas(desde) if opciones['etapas'] else (0, 0)
            if opciones['dry_run']:
                transaction.set_rollback(True)

        for nombre, n in self.sin_par.most_common():
            self.stdout.write(self.style.WARNING(f'  Sin equivalente en {hasta.slug}: «{nombre}» ({n})'))
        prefijo = '[dry-run, sin guardar] ' if opciones['dry_run'] else ''
        self.stdout.write(self.style.SUCCESS(
            f'{prefijo}{desde.slug} → {hasta.slug}: {apariciones} aparición(es), {relevancias} relevancia(s), '
            f'{etapas} etapa(s) nuevas y {imagenes} imagen(es) completadas.'
        ))

    def _obra(self, slug):
        obra = Obra.objects.filter(slug=slug).first()
        if obra is None:
            raise CommandError(f'Obra no encontrada: {slug}')
        return obra

    def _destino(self, unidad):
        while unidad is not None and unidad.tipo in HOJAS:
            unidad = unidad.padre
        if unidad is None:
            return None
        for clave in claves_origen(unidad.nombre):
            candidatas = self.indice.get(clave)
            if candidatas:
                # Si varias coinciden (Reliquias I y II), la última: nunca adelanta una aparición.
                return candidatas[-1]
        self.sin_par[unidad.nombre] += 1
        return None

    def _apariciones(self, desde):
        nuevas = 0
        propuestas = (
            PropuestaAparicion.objects
            .filter(unidad__obra=desde, estado=PropuestaAparicion.ESTADO_APROBADA)
            .select_related('personaje', 'unidad__padre')
        )
        for propuesta in propuestas:
            destino = self._destino(propuesta.unidad)
            if destino is None:
                continue
            copia, _ = PropuestaAparicion.objects.get_or_create(
                personaje=propuesta.personaje, unidad=destino,
                defaults={'origen': PropuestaAparicion.ORIGEN_MANUAL, 'nota': f'Copiada de {desde.titulo}'},
            )
            if copia.estado != PropuestaAparicion.ESTADO_APROBADA:
                aprobar_propuesta(copia)
                nuevas += 1
        return nuevas

    def _relevancias(self, desde, hasta):
        nuevas = 0
        for relevancia in RelevanciaPersonaje.objects.filter(obra=desde):
            _, creada = RelevanciaPersonaje.objects.get_or_create(
                personaje_id=relevancia.personaje_id, obra=hasta, defaults={'nivel': relevancia.nivel},
            )
            nuevas += creada
        return nuevas

    def _etapas(self, desde):
        nuevas = imagenes = 0
        # De la más tardía a la más temprana: si dos caen en la misma unidad destino, gana el estado final.
        etapas = (
            EtapaPersonaje.objects.filter(visible_tras__obra=desde)
            .select_related('visible_tras__padre').order_by('-visible_tras__orden_fin')
        )
        for etapa in etapas:
            destino = self._destino(etapa.visible_tras)
            if destino is None:
                continue
            copia, creada = EtapaPersonaje.objects.get_or_create(
                personaje_id=etapa.personaje_id, visible_tras=destino,
                defaults={
                    'alias': etapa.alias, 'nota': etapa.nota, 'nivel': etapa.nivel,
                    'imagen': etapa.imagen.name or None,
                },
            )
            if creada:
                nuevas += 1
            elif not copia.imagen and etapa.imagen:
                copia.imagen = etapa.imagen.name
                copia.save(update_fields=['imagen'])
                imagenes += 1
        return nuevas, imagenes