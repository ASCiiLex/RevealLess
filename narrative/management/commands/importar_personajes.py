import os
import re

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from narrative.models import ExternalId, Obra, Personaje, PropuestaAparicion
from narrative.services import jikan_client as jikan
from narrative.services import wikidata_client as wikidata
from narrative.services.apariciones_ia import (
    ErrorApariciones,
    proponer_personajes,
    proponer_primeras_apariciones,
)
from narrative.services.personajes import aprobar_propuesta

LOTE_IA = 25
RE_QID = re.compile(r'^Q\d+$')
# Wikidata guarda varios estrenos (premieres, países); se usa el más cercano al del catálogo.
VENTANA_DIAS = 21
# Obras de películas descartan partes de televisión, y al revés.
CLASE_EXCLUIDA = {
    Obra.TIPO_PELICULA: wikidata.CLASE_TV,
    Obra.TIPO_SERIE: wikidata.CLASE_PELICULA,
    Obra.TIPO_OVA: wikidata.CLASE_PELICULA,
}


def variantes_titulo(titulo):
    """Título tal cual, sin paréntesis y sin lo que sigue a los dos puntos."""
    sin_parentesis = re.sub(r'\s*\([^)]*\)', '', titulo).strip()
    variantes = [titulo, sin_parentesis, sin_parentesis.split(':')[0].strip()]
    return list(dict.fromkeys(v for v in variantes if v))


def _distancia(parte, unidad):
    return min(abs((f - unidad.fecha).days) for f in parte['fechas'])


def emparejar(partes, unidades, ventana=VENTANA_DIAS):
    """Parte de Wikidata → unidad, uno a uno. Primero por título exacto; después por la
    fecha más cercana dentro de la ventana, de la pareja más cercana a la más lejana (a
    igual distancia, la parte con más personajes) para que una parte ajena no robe la unidad."""
    emparejadas, usadas = {}, set()

    por_titulo = {}
    for u in unidades:
        por_titulo.setdefault(slugify(u.nombre), u)
    for parte in partes:
        unidad = por_titulo.get(slugify(parte['titulo']))
        if unidad and unidad.id not in usadas:
            emparejadas[parte['qid']] = unidad
            usadas.add(unidad.id)

    con_fecha = [u for u in unidades if u.fecha]
    parejas = sorted(
        (_distancia(parte, u), -len(parte['personajes']), parte['qid'], u.id, u)
        for parte in partes
        if parte['fechas'] and parte['qid'] not in emparejadas
        for u in con_fecha
        if _distancia(parte, u) <= ventana
    )
    for _, _, qid, _, unidad in parejas:
        if qid not in emparejadas and unidad.id not in usadas:
            emparejadas[qid] = unidad
            usadas.add(unidad.id)
    return emparejadas


class Command(BaseCommand):
    help = (
        'Importa personajes de Wikidata, Jikan y, opcionalmente, Haiku. Las apariciones por '
        'película/episodio de Wikidata entran aprobadas; la primera aparición del resto la '
        'propone Haiku y queda pendiente de revisión.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--obra', help='Slug de la obra. Si se omite, todo el catálogo.')
        parser.add_argument('--qid', help='Fija el identificador Q de Wikidata de la obra (requiere --obra).')
        parser.add_argument('--buscar-qid', action='store_true', help='Lista candidatos de Wikidata y sale.')
        parser.add_argument('--texto', help='Con --buscar-qid: texto a buscar en lugar del título.')
        parser.add_argument('--solo-wikidata', action='store_true', help='Sin Jikan ni Haiku.')
        parser.add_argument('--sin-jikan', action='store_true', help='No consulta personajes de Jikan.')
        parser.add_argument('--max-personajes', type=int, default=30, help='Máximo de personajes de Jikan por obra.')
        parser.add_argument(
            '--completar-ia', type=int, default=0, metavar='N',
            help='Pide a Haiku hasta N personajes principales que falten (quedan pendientes de revisión).',
        )
        parser.add_argument('--forzar', action='store_true', help='Vuelve a proponer aunque ya haya apariciones en la obra.')
        parser.add_argument('--dry-run', action='store_true', help='Consulta las fuentes sin escribir ni llamar a Haiku.')

    def handle(self, *args, **options):
        obras = Obra.objects.order_by('titulo')
        if options['obra']:
            obras = obras.filter(slug=options['obra'])
            if not obras.exists():
                raise CommandError(f'No existe una obra con slug "{options["obra"]}".')
        elif options['qid'] or options['buscar_qid']:
            raise CommandError('--qid y --buscar-qid requieren --obra.')

        if options['buscar_qid']:
            self._buscar_qid(obras.get(), options['texto'])
            return

        if options['qid']:
            if not RE_QID.match(options['qid']):
                raise CommandError('El QID debe tener la forma Q123.')
            ExternalId.objects.update_or_create(
                source=ExternalId.SOURCE_WIKIDATA, obra=obras.get(), defaults={'external_id': options['qid']},
            )

        usa_ia = not options['solo_wikidata'] and not options['dry_run']
        if usa_ia and not os.environ.get('ANTHROPIC_API_KEY'):
            raise CommandError('ANTHROPIC_API_KEY no configurada (usa --solo-wikidata o --dry-run).')

        for obra in obras:
            self._procesar(obra, options)

    # -- búsqueda del QID ------------------------------------------------

    def _buscar_qid(self, obra, texto):
        vistos = set()
        for consulta in ([texto] if texto else variantes_titulo(obra.titulo)):
            for idioma in ('es', 'en'):
                for c in wikidata.buscar_entidades(consulta, idioma):
                    if c['id'] in vistos:
                        continue
                    vistos.add(c['id'])
                    self.stdout.write(f'  {c["id"]}  {c["label"]} — {c["descripcion"]}')
        if vistos:
            self.stdout.write('Fija el correcto con --qid Q…')
        else:
            self.stdout.write(self.style.WARNING('Sin candidatos. Prueba con --texto "…".'))

    # -- flujo por obra ----------------------------------------------------

    def _procesar(self, obra, options):
        unidades = list(obra.unidades.order_by('orden_inicio'))
        if not unidades:
            self.stdout.write(self.style.WARNING(f'{obra.titulo}: sin unidades, se omite.'))
            return

        dry = options['dry_run']
        con_ia = not options['solo_wikidata']
        qid = self._external_id(obra, ExternalId.SOURCE_WIKIDATA)
        mal_id = self._external_id(obra, ExternalId.SOURCE_JIKAN)
        usa_jikan = bool(mal_id) and con_ia and not options['sin_jikan']
        completar = options['completar_ia'] if con_ia else 0
        if not qid and not usa_jikan and not completar:
            if options['obra']:
                self.stdout.write(self.style.WARNING(f'{obra.titulo}: sin QID de Wikidata; usa --buscar-qid.'))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(obra.titulo))
        candidatos = {}
        aprobadas = 0

        if qid:
            try:
                aprobadas = self._desde_wikidata(obra, qid, unidades, candidatos, dry)
            except wikidata.WikidataError as e:
                self.stderr.write(self.style.WARNING(f'  Wikidata: {e}'))

        if usa_jikan:
            tipo = 'manga' if obra.tipo == Obra.TIPO_MANGA else 'anime'
            try:
                personajes = jikan.get_characters(mal_id, tipo)
                personajes.sort(key=lambda c: c['rol'] != 'Main')
                for c in personajes[:options['max_personajes']]:
                    nombre = c['nombre'].replace(', ', ' ').strip()
                    candidatos.setdefault(slugify(nombre), {'qid': None, 'nombre': nombre})
            except jikan.JikanError as e:
                self.stderr.write(self.style.WARNING(f'  Jikan: {e}'))

        if completar:
            if dry:
                self.stdout.write(f'  Haiku propondría hasta {completar} personajes principales más.')
            else:
                self._completar_con_ia(obra, candidatos, completar)

        pendientes = [c for c in candidatos.values() if options['forzar'] or not self._ya_ubicado(c, obra)]
        self.stdout.write(
            f'  Apariciones {"que se aprobarían" if dry else "aprobadas"} desde Wikidata: {aprobadas}. '
            f'Personajes sin primera aparición (irían a Haiku): {len(pendientes)}.'
        )

        if dry or not con_ia or not pendientes:
            return

        propuestas = 0
        for inicio in range(0, len(pendientes), LOTE_IA):
            lote = pendientes[inicio:inicio + LOTE_IA]
            try:
                resultado = proponer_primeras_apariciones(obra, {i: c['nombre'] for i, c in enumerate(lote)}, unidades)
            except ErrorApariciones as e:
                self.stderr.write(self.style.WARNING(f'  Haiku: lote {inicio}-{inicio + len(lote)} omitido ({e}).'))
                continue
            for i, datos in resultado.items():
                c = lote[i]
                # Sin QID (Jikan o Haiku): se adopta el nombre en español que propone Haiku.
                nombre = c['nombre'] if c['qid'] else (datos['nombre'] or c['nombre'])
                personaje = self._personaje(nombre, c['qid'])
                propuesta, creada = PropuestaAparicion.objects.get_or_create(
                    personaje=personaje, unidad_id=datos['unidad_id'],
                    defaults={
                        'origen': PropuestaAparicion.ORIGEN_IA,
                        'confianza': datos['confianza'], 'nota': datos['nota'],
                    },
                )
                if not creada and propuesta.estado == PropuestaAparicion.ESTADO_PENDIENTE:
                    propuesta.confianza, propuesta.nota = datos['confianza'], datos['nota']
                    propuesta.save(update_fields=['confianza', 'nota'])
                propuestas += 1

        self.stdout.write(self.style.SUCCESS(f'  Propuestas de Haiku pendientes de revisión: {propuestas}.'))

    def _desde_wikidata(self, obra, qid, unidades, candidatos, dry):
        excluida = CLASE_EXCLUIDA.get(obra.tipo)
        todas = wikidata.partes_de_obra(qid)
        partes = [p for p in todas if p['clase'] != excluida]
        emparejadas = emparejar(partes, unidades)

        aprobadas = 0
        for parte in partes:
            unidad = emparejadas.get(parte['qid'])
            if unidad is None:
                continue
            if not dry:
                ExternalId.objects.get_or_create(
                    source=ExternalId.SOURCE_WIKIDATA, unidad=unidad, defaults={'external_id': parte['qid']},
                )
            for p in parte['personajes']:
                if RE_QID.match(p['nombre']):
                    continue  # sin etiqueta utilizable
                aprobadas += 1 if dry else self._aprobar_wikidata(p, unidad)

        descartadas = len(todas) - len(partes)
        self.stdout.write(
            f'  Wikidata: {len(emparejadas)}/{len(partes)} partes emparejadas'
            + (f' ({descartadas} de otro formato descartadas).' if descartadas else '.')
        )
        if dry:
            self._informe(partes, emparejadas)

        for p in wikidata.personajes_de_obra(qid):
            if not RE_QID.match(p['nombre']):
                candidatos[slugify(p['nombre'])] = p
        return aprobadas

    def _completar_con_ia(self, obra, candidatos, maximo):
        conocidos = [c['nombre'] for c in candidatos.values()]
        conocidos += list(
            Personaje.objects.filter(unidades__obra=obra).distinct().values_list('nombre', flat=True)
        )
        try:
            nuevos = proponer_personajes(obra, conocidos, maximo)
        except ErrorApariciones as e:
            self.stderr.write(self.style.WARNING(f'  Haiku (personajes): {e}'))
            return
        for nombre in nuevos:
            candidatos.setdefault(slugify(nombre), {'qid': None, 'nombre': nombre})
        self.stdout.write(f'  Haiku propone {len(nuevos)} personajes más.')

    def _informe(self, partes, emparejadas):
        """Emparejadas, y aparte las no emparejadas que traían personajes (lo que se pierde)."""
        for parte in sorted(partes, key=lambda p: p['fechas'][:1] or [None] and []):
            unidad = emparejadas.get(parte['qid'])
            if unidad:
                fecha = min(parte['fechas'], key=lambda f: abs((f - unidad.fecha).days)) \
                    if parte['fechas'] and unidad.fecha else 'sin fecha'
                self.stdout.write(
                    f'    ✓ {parte["titulo"]} ({fecha}) → {unidad.nombre} '
                    f'({unidad.fecha or "sin fecha"}) · {len(parte["personajes"])} personajes'
                )
        perdidas = [p for p in partes if p['qid'] not in emparejadas and p['personajes']]
        if perdidas:
            self.stdout.write('  Sin emparejar, con personajes:')
            for parte in perdidas:
                fechas = ', '.join(str(f) for f in parte['fechas']) or 'sin fecha'
                self.stdout.write(
                    f'    ✗ {parte["qid"]} {parte["titulo"]} ({fechas}) · {len(parte["personajes"])} personajes'
                )

    # -- utilidades --------------------------------------------------------

    def _external_id(self, obra, source):
        externo = ExternalId.objects.filter(source=source, obra=obra).first()
        return externo.external_id if externo else None

    def _aprobar_wikidata(self, datos, unidad):
        personaje = self._personaje(datos['nombre'], datos['qid'])
        propuesta, _ = PropuestaAparicion.objects.get_or_create(
            personaje=personaje, unidad=unidad, defaults={'origen': PropuestaAparicion.ORIGEN_WIKIDATA},
        )
        if propuesta.estado != PropuestaAparicion.ESTADO_PENDIENTE:
            return 0  # ya aprobada, o rechazada a mano: se respeta
        aprobar_propuesta(propuesta)
        return 1

    def _ya_ubicado(self, candidato, obra):
        personaje = self._buscar_personaje(candidato['nombre'], candidato['qid'])
        return personaje is not None and (
            personaje.unidades.filter(obra=obra).exists()
            or personaje.propuestas.filter(unidad__obra=obra).exists()
        )

    def _buscar_personaje(self, nombre, qid):
        if qid:
            personaje = Personaje.objects.filter(wikidata_id=qid).first()
            if personaje:
                return personaje
        personaje = Personaje.objects.filter(nombre__iexact=nombre).first()
        if personaje and qid and personaje.wikidata_id and personaje.wikidata_id != qid:
            return None  # mismo nombre, otro personaje
        return personaje

    def _personaje(self, nombre, qid):
        personaje = self._buscar_personaje(nombre, qid)
        if personaje:
            if qid and not personaje.wikidata_id:
                personaje.wikidata_id = qid
                personaje.save(update_fields=['wikidata_id'])
            return personaje
        if Personaje.objects.filter(nombre__iexact=nombre).exists():
            nombre = f'{nombre} ({qid})'
        return Personaje.objects.create(nombre=nombre[:150], wikidata_id=qid)