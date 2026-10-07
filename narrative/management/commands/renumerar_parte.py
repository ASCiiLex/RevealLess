import re

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from narrative.models import Obra, UnidadNarrativa

# Nombre con número final: «Episodio 221», «Capítulo 701».
PATRON_NUMERADO = re.compile(r'^(?P<prefijo>.*?)(?P<numero>\d+)$')
SEPARADOR = ' · '


class Command(BaseCommand):
    help = (
        'Reinicia desde 1 la numeración de los episodios o capítulos de una parte de la obra '
        '(ej. Shippūden tras Naruto) y, si se indica, antepone un prefijo a sus temporadas. '
        'Solo cambia nombres: ids, orden, apariciones, etapas, progreso y posts no se tocan.'
    )

    def add_arguments(self, parser):
        parser.add_argument('obra', help='Slug de la obra.')
        parser.add_argument('parte', help='Nombre exacto de la unidad raíz que se renumera.')
        parser.add_argument(
            '--prefijo-temporadas', default='',
            help='Ej. "Shippūden": «Temporada 1» pasa a «Shippūden · Temporada 1».',
        )
        parser.add_argument('--dry-run', action='store_true', help='Muestra los cambios sin guardarlos.')

    def handle(self, *args, **opciones):
        obra = Obra.objects.filter(slug=opciones['obra']).first()
        if obra is None:
            raise CommandError(f'No existe la obra «{opciones["obra"]}».')
        parte = UnidadNarrativa.objects.filter(obra=obra, padre=None, nombre=opciones['parte']).first()
        if parte is None:
            raise CommandError(f'La obra no tiene una parte raíz llamada «{opciones["parte"]}».')

        cambios = self._renombrar_hojas(obra, parte) + self._renombrar_temporadas(parte, opciones['prefijo_temporadas'])
        if not cambios:
            self.stdout.write('Nada que cambiar: la parte ya está renumerada.')
            return

        for unidad, anterior in cambios[:5] + ([] if len(cambios) <= 10 else [(None, None)]) + cambios[-5:]:
            if unidad is None:
                self.stdout.write('   …')
            else:
                self.stdout.write(f'   {anterior} → {unidad.nombre}')

        if opciones['dry_run']:
            self.stdout.write(self.style.WARNING(f'[dry-run] {len(cambios)} unidad(es) cambiarían de nombre.'))
            return

        with transaction.atomic():
            UnidadNarrativa.objects.bulk_update([u for u, _ in cambios], ['nombre'])
        self.stdout.write(self.style.SUCCESS(f'{len(cambios)} unidad(es) renombrada(s).'))

    def _renombrar_hojas(self, obra, parte):
        hojas = list(
            UnidadNarrativa.objects.filter(
                obra=obra, orden_inicio__gte=parte.orden_inicio, orden_fin__lte=parte.orden_fin,
                hijos__isnull=True,
            ).distinct().order_by('orden_inicio')
        )
        numeradas = [(h, PATRON_NUMERADO.match(h.nombre)) for h in hojas]
        numeradas = [(h, m) for h, m in numeradas if m]
        sin_numero = len(hojas) - len(numeradas)
        if sin_numero:
            self.stdout.write(self.style.WARNING(f'{sin_numero} unidad(es) sin número final: se dejan igual.'))
        if not numeradas:
            return []

        desfase = min(int(m['numero']) for _, m in numeradas) - 1
        if desfase <= 0:
            return []

        cambios = []
        for hoja, m in numeradas:
            anterior = hoja.nombre
            hoja.nombre = f'{m["prefijo"]}{int(m["numero"]) - desfase}'
            cambios.append((hoja, anterior))
        return cambios

    def _renombrar_temporadas(self, parte, prefijo):
        prefijo = prefijo.strip()
        if not prefijo:
            return []
        cambios = []
        for temporada in parte.hijos.filter(hijos__isnull=False).distinct().order_by('orden_local'):
            if temporada.nombre.startswith(f'{prefijo}{SEPARADOR}'):
                continue
            anterior = temporada.nombre
            temporada.nombre = f'{prefijo}{SEPARADOR}{anterior}'
            cambios.append((temporada, anterior))
        return cambios