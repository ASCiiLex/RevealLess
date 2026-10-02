from pathlib import Path

import yaml
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from narrative.models import EtapaPersonaje, Obra, Personaje, UnidadNarrativa

CAMPOS = ('alias', 'nota', 'nivel')


class Command(BaseCommand):
    help = ('Crea o actualiza etapas de personaje desde un YAML (recompensas, alias, niveles). '
            'Solo escribe los campos del fichero: las imágenes ya subidas se conservan.')

    def add_arguments(self, parser):
        parser.add_argument('fichero')
        parser.add_argument('--dry-run', action='store_true', help='Muestra el resultado sin guardar.')

    def handle(self, *args, **opciones):
        ruta = Path(opciones['fichero'])
        if not ruta.exists():
            raise CommandError(f'No existe {ruta}')
        datos = yaml.safe_load(ruta.read_text(encoding='utf-8'))
        tipo = datos.get('tipo_unidad', 'arco')
        simular = opciones['dry_run']

        obras = list(Obra.objects.filter(slug__in=datos['obras']))
        for slug in set(datos['obras']) - {o.slug for o in obras}:
            self.stdout.write(self.style.WARNING(f'Obra no encontrada: {slug}'))

        cuenta = {'creadas': 0, 'actualizadas': 0, 'saltadas': 0}
        with transaction.atomic():
            for entrada in datos['etapas']:
                personaje = self._personaje(entrada['personaje'])
                if personaje is None:
                    self.stdout.write(self.style.WARNING(f'Personaje no encontrado: {entrada["personaje"]}'))
                    cuenta['saltadas'] += len(obras)
                    continue
                campos = {c: entrada[c] for c in CAMPOS if c in entrada}
                for obra in obras:
                    unidad = (
                        UnidadNarrativa.objects.filter(obra=obra, tipo=tipo, nombre__iregex=entrada['tras'])
                        .order_by('orden_fin').last()
                    )
                    if unidad is None:
                        self.stdout.write(self.style.WARNING(f'  [{obra.slug}] sin {tipo} que coincida con «{entrada["tras"]}»'))
                        cuenta['saltadas'] += 1
                        continue
                    existe = EtapaPersonaje.objects.filter(personaje=personaje, visible_tras=unidad).exists()
                    if not simular:
                        EtapaPersonaje.objects.update_or_create(personaje=personaje, visible_tras=unidad, defaults=campos)
                    cuenta['actualizadas' if existe else 'creadas'] += 1
                    self.stdout.write(f'  [{obra.slug}] {personaje.nombre} tras {unidad.nombre}: {campos}')

        prefijo = '[dry-run] ' if simular else ''
        self.stdout.write(self.style.SUCCESS(
            f'{prefijo}{cuenta["creadas"]} creada(s), {cuenta["actualizadas"]} actualizada(s), {cuenta["saltadas"]} saltada(s).'
        ))

    def _personaje(self, referencia):
        if isinstance(referencia, int):
            return Personaje.objects.filter(id=referencia).first()
        return (
            Personaje.objects.filter(nombre__iexact=referencia).first()
            or Personaje.objects.filter(etapas__alias__iexact=referencia).distinct().first()
        )