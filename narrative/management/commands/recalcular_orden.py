from django.core.management.base import BaseCommand, CommandError
from narrative.models import Obra


class Command(BaseCommand):
    help = 'Recalcula orden_inicio/orden_fin de las unidades narrativas de una obra.'

    def add_arguments(self, parser):
        parser.add_argument('slug', nargs='?', help='Slug de la obra. Si se omite, recalcula todas.')

    def handle(self, *args, **options):
        slug = options.get('slug')
        obras = Obra.objects.filter(slug=slug) if slug else Obra.objects.all()
        if slug and not obras.exists():
            raise CommandError(f'No existe una obra con slug "{slug}".')
        for obra in obras:
            obra.recalcular_orden()
            self.stdout.write(self.style.SUCCESS(f'Recalculado: {obra.titulo}'))