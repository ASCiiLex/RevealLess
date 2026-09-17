from django.core.management.base import BaseCommand
from django.utils.text import slugify

from narrative.models import Obra, ExternalId, Categoria


class Command(BaseCommand):
    help = (
        'Crea (o localiza) una Obra sin fuente externa y le asigna un '
        "ExternalId(source='manual') para que importar_estructura pueda "
        'aplicarle un YAML de curación exactamente igual que a una Obra '
        'importada de Jikan.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--slug', required=True)
        parser.add_argument('--titulo', required=True)
        parser.add_argument('--tipo', default=Obra.TIPO_SERIE, choices=[t for t, _ in Obra.TIPO_CHOICES])
        parser.add_argument('--sinopsis', default='')
        parser.add_argument('--autor', default='')
        parser.add_argument('--fecha-publicacion', default=None, help='YYYY-MM-DD')
        parser.add_argument(
            '--categoria', action='append', default=[],
            help='Nombre de Categoria a asignar (repetible: --categoria X --categoria Y).',
        )

    def handle(self, *args, **options):
        slug = options['slug'] or slugify(options['titulo'])

        obra, creada = Obra.objects.get_or_create(
            slug=slug,
            defaults={
                'titulo': options['titulo'],
                'tipo': options['tipo'],
                'sinopsis': options['sinopsis'],
                'autor': options['autor'],
                'fecha_publicacion': options['fecha_publicacion'],
            },
        )
        externo, _ = ExternalId.objects.get_or_create(
            source=ExternalId.SOURCE_MANUAL, external_id=slug, obra=obra,
        )

        for nombre in options['categoria']:
            categoria, _ = Categoria.objects.get_or_create(nombre=nombre)
            obra.categorias.add(categoria)

        verbo = 'Creada' if creada else 'Ya existía'
        self.stdout.write(self.style.SUCCESS(f'{verbo}: {obra.titulo} (slug={slug})'))