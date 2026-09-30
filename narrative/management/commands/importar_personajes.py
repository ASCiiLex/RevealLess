import os
import re
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from narrative.models import ExternalId, Obra, Personaje, PropuestaAparicion
from narrative.services import jikan_client as jikan
from narrative.services import wikidata_client as wikidata
from narrative.services.apariciones_ia import ErrorApariciones, proponer_primeras_apariciones
from narrative.services.personajes import aprobar_propuesta

LOTE_IA = 25
RE_QID = re.compile(r'^Q\d+$')


class Command(BaseCommand):
    help = (
        'Importa personajes de Wikidata y Jikan. Las apariciones por película/episodio de Wikidata '
        'entran aprobadas; la primera aparición del resto la propone Haiku y queda pendiente de revisión.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--obra', help='Slug de la obra. Si se omite, todo el catálogo.')
        parser.add_argument('--qid', help='Fija el identificador Q de Wikidata de la obra (requiere --obra).')
        parser.add_argument('--buscar-qid', action='store_true', help='Lista candidatos de Wikidata y sale.')
        parser.add_argument('--solo-wikidata', action='store_true', help='Sin Jikan ni Haiku.')
        parser.add_argument('--sin-jikan', action='store_true', help='No consulta personajes de Jikan.')
        parser.add_argument('--max-personajes', type=int, default=30, help='Máximo de personajes de Jikan por obra.')
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
            self._buscar_qid(obras.get())
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

    def _buscar_qid(self, obra):
        for idioma in ('es', 'en'):
            self.stdout.write(f'Candidatos ({idioma}) para "{obra.titulo}":')
            for c in wikidata.buscar_entidades(obra.titulo, idioma):
                self.stdout.write(f'  {c["id"]}  {c["label"]} — {c["descripcion"]}')
        self.stdout.write('Fija el correcto con --qid Q…')

    # -- flujo por obra ----------------------------------------------------

    def _procesar(self, obra, options):
        unidades = list(obra.unidades.order_by('orden_inicio'))
        if not unidades:
            self.stdout.write(self.style.WARNING(f'{obra.titulo}: sin unidades, se omite.'))
            return

        dry = options['dry_run']
        qid = self._external_id(obra, ExternalId.SOURCE_WIKIDATA)
        mal_id = self._external_id(obra, ExternalId.SOURCE_JIKAN)
        if not qid and not (mal_id and not options['solo_wikidata'] and not options['sin_jikan']):
            if options['obra']:
                self.stdout.write(self.style.WARNING(f'{obra.titulo}: sin QID de Wikidata; usa --buscar-qid.'))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(obra.titulo))
        candidatos = {}
        aprobadas = 0

        if qid:
            try:
                partes = wikidata.partes_de_obra(qid)
                emparejadas = self._emparejar(partes, unidades)
                for parte in partes:
                    unidad = emparejadas.get(parte['qid'])
                    if unidad is None:
                        continue
                    if not dry:
                        ExternalId.objects.get_or_create(
                            source=ExternalId.SOURCE_WIKIDATA, unidad=unidad,
                            defaults={'external_id': parte['qid']},
                        )
                    for p in parte['personajes']:
                        if RE_QID.match(p['nombre']):
                            continue  # sin etiqueta en es/en
                        aprobadas += 1 if dry else self._aprobar_wikidata(p, unidad)
                self.stdout.write(f'  Wikidata: {len(emparejadas)}/{len(partes)} partes emparejadas.')

                for p in wikidata.personajes_de_obra(qid):
                    if not RE_QID.match(p['nombre']):
                        candidatos[slugify(p['nombre'])] = p
            except wikidata.WikidataError as e:
                self.stderr.write(self.style.WARNING(f'  Wikidata: {e}'))

        if mal_id and not options['solo_wikidata'] and not options['sin_jikan']:
            tipo = 'manga' if obra.tipo == Obra.TIPO_MANGA else 'anime'
            try:
                personajes = jikan.get_characters(mal_id, tipo)
                personajes.sort(key=lambda c: c['rol'] != 'Main')
                for c in personajes[:options['max_personajes']]:
                    nombre = c['nombre'].replace(', ', ' ').strip()
                    candidatos.setdefault(slugify(nombre), {'qid': None, 'nombre': nombre})
            except jikan.JikanError as e:
                self.stderr.write(self.style.WARNING(f'  Jikan: {e}'))

        pendientes = [c for c in candidatos.values() if options['forzar'] or not self._ya_ubicado(c, obra)]
        self.stdout.write(
            f'  Apariciones aprobadas desde Wikidata: {aprobadas}. '
            f'Personajes sin primera aparición: {len(pendientes)}.'
        )

        if dry or options['solo_wikidata'] or not pendientes:
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
                # Sin QID (vino de Jikan): se adopta el nombre en español que propone Haiku.
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

    # -- utilidades --------------------------------------------------------

    def _external_id(self, obra, source):
        externo = ExternalId.objects.filter(source=source, obra=obra).first()
        return externo.external_id if externo else None

    def _emparejar(self, partes, unidades):
        """Parte de Wikidata → unidad: por fecha de estreno única; si no, por título."""
        por_fecha = defaultdict(list)
        for u in unidades:
            if u.fecha:
                por_fecha[u.fecha].append(u)
        por_titulo = {slugify(u.nombre): u for u in unidades}

        emparejadas = {}
        for parte in partes:
            mismas = por_fecha.get(parte['fecha'], []) if parte['fecha'] else []
            if len(mismas) == 1:
                emparejadas[parte['qid']] = mismas[0]
                continue
            titulo = slugify(parte['titulo'])
            elegida = next((u for u in mismas if slugify(u.nombre) == titulo), None) or por_titulo.get(titulo)
            if elegida:
                emparejadas[parte['qid']] = elegida
        return emparejadas

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