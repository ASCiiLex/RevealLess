import os
import re

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Min
from django.utils.text import slugify

from narrative.models import ExternalId, Obra, Personaje, PropuestaAparicion
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
# Partes de Wikidata que no pueden corresponder a unidades de cada tipo de obra.
EXCLUIDAS_POR_TIPO = {
    Obra.TIPO_PELICULA: {wikidata.CLASE_TV, wikidata.CLASE_AGRUPACION},
    Obra.TIPO_SERIE: {wikidata.CLASE_PELICULA, wikidata.CLASE_AGRUPACION},
    Obra.TIPO_OVA: {wikidata.CLASE_PELICULA, wikidata.CLASE_AGRUPACION},
}
EXCLUIDAS_POR_DEFECTO = {wikidata.CLASE_AGRUPACION}


def variantes_titulo(titulo):
    """Título tal cual, sin paréntesis y sin lo que sigue a los dos puntos."""
    sin_parentesis = re.sub(r'\s*\([^)]*\)', '', titulo).strip()
    variantes = [titulo, sin_parentesis, sin_parentesis.split(':')[0].strip()]
    return list(dict.fromkeys(v for v in variantes if v))


def _distancia(parte, unidad):
    return min(abs((f - unidad.fecha).days) for f in parte['fechas'])


def emparejar(partes, unidades, ventana=VENTANA_DIAS):
    """Parte de Wikidata → unidad, uno a uno. Primero por título exacto. Después por fecha,
    solo para partes con personajes (lo único que se importa) y solo sin empates: con varios
    episodios estrenados el mismo día (Netflix) no hay forma fiable de saber cuál es cuál."""
    emparejadas, usadas = {}, set()

    por_titulo = {}
    for u in unidades:
        por_titulo.setdefault(slugify(u.nombre), u)
    for parte in partes:
        unidad = por_titulo.get(slugify(parte['titulo']))
        if unidad and unidad.id not in usadas:
            emparejadas[parte['qid']] = unidad
            usadas.add(unidad.id)

    candidatas = [p for p in partes if p['fechas'] and p['personajes'] and p['qid'] not in emparejadas]
    libres = [u for u in unidades if u.fecha and u.id not in usadas]
    distancias = {}
    for parte in candidatas:
        for u in libres:
            d = _distancia(parte, u)
            if d <= ventana:
                distancias[(parte['qid'], u.id)] = d
    por_id = {u.id: u for u in libres}

    for (qid, uid), d in sorted(distancias.items(), key=lambda item: item[1]):
        if qid in emparejadas or uid in usadas:
            continue
        otra_unidad = any(q == qid and u != uid and dd <= d for (q, u), dd in distancias.items())
        otra_parte = any(u == uid and q != qid and dd <= d for (q, u), dd in distancias.items())
        if otra_unidad or otra_parte:
            continue  # empate: ambiguo, mejor sin emparejar
        emparejadas[qid] = por_id[uid]
        usadas.add(uid)
    return emparejadas


class Command(BaseCommand):
    help = (
        'Importa personajes de Wikidata y, opcionalmente, Haiku. Las apariciones por '
        'película/episodio de Wikidata entran aprobadas; Haiku propone la primera aparición '
        'cuando adelanta la conocida, siempre pendiente de revisión. '
        '(Jikan se descartó como fuente de personajes: su API respondía 504 de forma sostenida.)'
    )

    def add_arguments(self, parser):
        parser.add_argument('--obra', help='Slug de la obra. Si se omite, todo el catálogo.')
        parser.add_argument('--qid', help='Fija el identificador Q de Wikidata de la obra (requiere --obra).')
        parser.add_argument('--buscar-qid', action='store_true', help='Lista candidatos de Wikidata y sale.')
        parser.add_argument('--texto', help='Con --buscar-qid: texto a buscar en lugar del título.')
        parser.add_argument('--solo-wikidata', action='store_true', help='Sin Haiku.')
        parser.add_argument(
            '--max-wikidata', type=int, default=100,
            help='Si la lista de personajes de la obra en Wikidata es mayor, se ignora (reparto completo).',
        )
        parser.add_argument(
            '--completar-ia', type=int, default=0, metavar='N',
            help='Pide a Haiku hasta N personajes principales que falten (quedan pendientes de revisión).',
        )
        parser.add_argument('--forzar', action='store_true', help='Vuelve a pedir a Haiku aunque ya lo hiciera.')
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
        completar = options['completar_ia'] if con_ia else 0
        if not qid and not completar:
            if options['obra']:
                self.stdout.write(self.style.WARNING(f'{obra.titulo}: sin QID de Wikidata; usa --buscar-qid.'))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(obra.titulo))
        candidatos = {}
        aprobadas = 0

        if qid:
            try:
                aprobadas = self._desde_wikidata(obra, qid, unidades, candidatos, options)
            except wikidata.WikidataError as e:
                self.stderr.write(self.style.WARNING(f'  Wikidata: {e}'))

        if completar:
            if dry:
                self.stdout.write(f'  Haiku propondría hasta {completar} personajes principales más.')
            else:
                self._completar_con_ia(obra, candidatos, completar)

        pendientes = [c for c in candidatos.values() if options['forzar'] or not self._ya_consultado(c, obra)]
        self.stdout.write(
            f'  Apariciones {"que se aprobarían" if dry else "aprobadas"} desde Wikidata: {aprobadas}. '
            f'Personajes para los que Haiku buscaría la primera aparición: {len(pendientes)}.'
        )

        if dry or not con_ia or not pendientes:
            return
        self._proponer_apariciones(obra, unidades, pendientes)

    def _desde_wikidata(self, obra, qid, unidades, candidatos, options):
        excluidas = EXCLUIDAS_POR_TIPO.get(obra.tipo, EXCLUIDAS_POR_DEFECTO)
        todas = wikidata.partes_de_obra(qid)
        partes = [p for p in todas if p['clase'] not in excluidas]
        emparejadas = emparejar(partes, unidades)

        aprobadas = 0
        for parte in partes:
            unidad = emparejadas.get(parte['qid'])
            if unidad is None:
                continue
            if not options['dry_run']:
                ExternalId.objects.get_or_create(
                    source=ExternalId.SOURCE_WIKIDATA, unidad=unidad, defaults={'external_id': parte['qid']},
                )
            for p in parte['personajes']:
                if RE_QID.match(p['nombre']):
                    continue  # sin etiqueta utilizable
                candidatos.setdefault(slugify(p['nombre']), p)
                aprobadas += 1 if options['dry_run'] else self._aprobar_wikidata(p, unidad)

        descartadas = len(todas) - len(partes)
        self.stdout.write(
            f'  Wikidata: {len(emparejadas)}/{len(partes)} partes emparejadas'
            + (f' ({descartadas} temporadas o de otro formato descartadas).' if descartadas else '.')
        )
        if options['dry_run']:
            self._informe(partes, emparejadas)

        lista = [p for p in wikidata.personajes_de_obra(qid) if not RE_QID.match(p['nombre'])]
        if len(lista) > options['max_wikidata']:
            self.stdout.write(self.style.WARNING(
                f'  Wikidata lista {len(lista)} personajes (reparto completo): se ignora esa lista; '
                'usa --completar-ia para los principales.'
            ))
        else:
            for p in lista:
                candidatos.setdefault(slugify(p['nombre']), p)
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

    def _proponer_apariciones(self, obra, unidades, pendientes):
        por_id = {u.id: u for u in unidades}
        propuestas = sin_mejora = 0
        for inicio in range(0, len(pendientes), LOTE_IA):
            lote = pendientes[inicio:inicio + LOTE_IA]
            try:
                resultado = proponer_primeras_apariciones(obra, {i: c['nombre'] for i, c in enumerate(lote)}, unidades)
            except ErrorApariciones as e:
                self.stderr.write(self.style.WARNING(f'  Haiku: lote {inicio}-{inicio + len(lote)} omitido ({e}).'))
                continue
            for i, datos in resultado.items():
                c = lote[i]
                # Sin QID (propuesto por Haiku): se adopta el nombre en español que devuelve.
                nombre = c['nombre'] if c['qid'] else (datos['nombre'] or c['nombre'])
                personaje = self._personaje(nombre, c['qid'])
                unidad = por_id[datos['unidad_id']]

                conocida = personaje.unidades.filter(obra=obra).aggregate(m=Min('orden_fin'))['m']
                if conocida is not None and conocida <= unidad.orden_fin:
                    sin_mejora += 1  # no adelanta la aparición ya aprobada
                    continue

                propuesta, creada = PropuestaAparicion.objects.get_or_create(
                    personaje=personaje, unidad=unidad,
                    defaults={
                        'origen': PropuestaAparicion.ORIGEN_IA,
                        'confianza': datos['confianza'], 'nota': datos['nota'],
                    },
                )
                if not creada and propuesta.estado == PropuestaAparicion.ESTADO_PENDIENTE:
                    propuesta.confianza, propuesta.nota = datos['confianza'], datos['nota']
                    propuesta.save(update_fields=['confianza', 'nota'])
                propuestas += 1

        self.stdout.write(self.style.SUCCESS(
            f'  Propuestas de Haiku pendientes de revisión: {propuestas} '
            f'({sin_mejora} descartadas por no adelantar la aparición conocida).'
        ))

    def _informe(self, partes, emparejadas):
        """Emparejadas, y aparte las no emparejadas que traían personajes (lo que se pierde)."""
        for parte in sorted(partes, key=lambda p: (not p['fechas'], p['fechas'][:1])):
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

    def _ya_consultado(self, candidato, obra):
        """Haiku ya propuso algo para este personaje en esta obra: no se repite sin --forzar."""
        personaje = self._buscar_personaje(candidato['nombre'], candidato['qid'])
        return personaje is not None and personaje.propuestas.filter(
            unidad__obra=obra, origen=PropuestaAparicion.ORIGEN_IA,
        ).exists()

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