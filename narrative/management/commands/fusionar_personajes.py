from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from narrative.models import Personaje
from narrative.services.personajes import fusionar_personajes


class Command(BaseCommand):
    help = 'Fusiona duplicados en un personaje: apariciones, propuestas, etapas, posts y suscripciones pasan al destino.'

    def add_arguments(self, parser):
        parser.add_argument('origenes', nargs='+', type=int, help='Ids de los duplicados (se borran).')
        parser.add_argument('--destino', type=int, required=True, help='Id del personaje que se conserva.')
        parser.add_argument('--dry-run', action='store_true', help='Simula sin guardar.')

    def handle(self, *args, origenes, destino, dry_run, **options):
        if destino in origenes:
            raise CommandError('El destino no puede estar entre los orígenes.')
        try:
            final = Personaje.objects.get(pk=destino)
        except Personaje.DoesNotExist:
            raise CommandError(f'No existe el personaje {destino}.')

        encontrados = Personaje.objects.in_bulk(origenes)
        for pk in sorted(set(origenes) - set(encontrados)):
            # Idempotente: un origen ya fusionado no detiene el resto.
            self.stdout.write(self.style.WARNING(f'  {pk}: no existe (¿ya fusionado?), se omite.'))

        with transaction.atomic():
            for pk in dict.fromkeys(origenes):
                if pk not in encontrados:
                    continue
                nombre = encontrados[pk].nombre
                fusionar_personajes(encontrados[pk], final)
                self.stdout.write(f'  {nombre} ({pk}) → {final.nombre}')
            total = final.unidades.count()
            if dry_run:
                transaction.set_rollback(True)

        prefijo = '[simulación] ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(f'{prefijo}{final.nombre} ({final.pk}): {total} apariciones.'))