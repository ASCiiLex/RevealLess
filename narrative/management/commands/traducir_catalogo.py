import os

from django.core.management.base import BaseCommand, CommandError

from narrative.models import Obra, UnidadNarrativa
from narrative.services.traduccion import ErrorTraduccion, traducir_textos

# Títulos provisionales de la importación: ya están en español.
REGEX_PROVISIONAL = r'^(Episodio|Capítulo) [0-9]+$'
LOTE_SINOPSIS = 5
LOTE_TITULOS = 40


class Command(BaseCommand):
    help = 'Traduce al español las sinopsis de obras y los títulos de unidades narrativas con Haiku.'

    def add_arguments(self, parser):
        parser.add_argument('--obra', help='Slug de una obra concreta. Si se omite, todo el catálogo.')
        parser.add_argument('--solo', choices=['sinopsis', 'unidades'], help='Traducir solo una de las dos partes.')
        parser.add_argument('--forzar', action='store_true', help='Retraducir también lo ya marcado como traducido.')
        parser.add_argument('--dry-run', action='store_true', help='Muestra qué se traduciría sin llamar a la API.')

    def handle(self, *args, **options):
        obras = Obra.objects.all()
        if options['obra']:
            obras = obras.filter(slug=options['obra'])
            if not obras.exists():
                raise CommandError(f'No existe una obra con slug "{options["obra"]}".')

        if not options['dry_run'] and not os.environ.get('ANTHROPIC_API_KEY'):
            raise CommandError('ANTHROPIC_API_KEY no configurada.')

        solo = options['solo']
        total = 0

        if solo in (None, 'sinopsis'):
            qs = obras.exclude(sinopsis='').order_by('titulo')
            if not options['forzar']:
                qs = qs.filter(traducido=False)
            total += self._procesar(list(qs), 'sinopsis', LOTE_SINOPSIS, options['dry_run'])

        if solo in (None, 'unidades'):
            qs = (
                UnidadNarrativa.objects.filter(obra__in=obras)
                .exclude(nombre__regex=REGEX_PROVISIONAL)
                .order_by('obra_id', 'orden_inicio')
            )
            if not options['forzar']:
                qs = qs.filter(traducido=False)
            total += self._procesar(list(qs), 'nombre', LOTE_TITULOS, options['dry_run'])

        if not options['dry_run']:
            self.stdout.write(self.style.SUCCESS(f'Traducidos {total} textos.'))

    def _procesar(self, objetos, campo, tamano_lote, dry_run):
        if not objetos:
            return 0

        modelo = type(objetos[0])
        nombre = modelo._meta.verbose_name_plural
        if dry_run:
            self.stdout.write(f'{nombre}: {len(objetos)} por traducir ({campo}).')
            return 0

        max_len = modelo._meta.get_field(campo).max_length
        hechos = 0
        for inicio in range(0, len(objetos), tamano_lote):
            lote = objetos[inicio:inicio + tamano_lote]
            try:
                traducciones = traducir_textos({o.id: getattr(o, campo) for o in lote})
            except ErrorTraduccion as e:
                self.stderr.write(self.style.WARNING(f'{nombre}: lote {inicio}-{inicio + len(lote)} omitido ({e}).'))
                continue

            modificados = []
            for obj in lote:
                if obj.id in traducciones:
                    texto = traducciones[obj.id]
                    setattr(obj, campo, texto[:max_len] if max_len else texto)
                    obj.traducido = True
                    modificados.append(obj)
            modelo.objects.bulk_update(modificados, [campo, 'traducido'])
            hechos += len(modificados)
            self.stdout.write(f'{nombre}: {hechos}/{len(objetos)}')
        return hechos