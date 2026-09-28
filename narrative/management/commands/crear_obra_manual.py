from django.core.management.base import BaseCommand
from django.utils.text import slugify

from narrative.models import Obra, ExternalId, Categoria

# Sufijo de nombre por tipo — (singular, plural). El slug nunca lleva
# sufijo; solo el titulo visible, para distinguir "Harry Potter (Libros)"
# de "Harry Potter (Películas)" cuando dos Obras comparten título base.
SUFIJOS_TIPO = {
    Obra.TIPO_SERIE: ('Serie', 'Series'),
    Obra.TIPO_PELICULA: ('Película', 'Películas'),
    Obra.TIPO_ESPECIAL: ('Especial', 'Especiales'),
    Obra.TIPO_OVA: ('OVA', 'OVA'),
    Obra.TIPO_CORTO: ('Corto', 'Cortos'),
    Obra.TIPO_MANGA: ('Manga', 'Manga'),
    Obra.TIPO_LIBRO: ('Libro', 'Libros'),
}

# Categoria que se añade automáticamente según el tipo, además de las
# pasadas por --categoria. Se reutiliza si ya existe (por nombre), igual
# que cualquier otra Categoria — nunca se duplica.
CATEGORIA_AUTO_TIPO = {
    Obra.TIPO_SERIE: 'Series',
    Obra.TIPO_PELICULA: 'Películas',
    Obra.TIPO_ESPECIAL: 'Especiales',
    Obra.TIPO_OVA: 'OVA',
    Obra.TIPO_CORTO: 'Cortos',
    Obra.TIPO_MANGA: 'Manga',
    Obra.TIPO_LIBRO: 'Libros',
}

ETIQUETAS_ANIME = {'anime'}


class Command(BaseCommand):
    help = (
        'Crea (o localiza) una Obra sin fuente externa y le asigna un '
        "ExternalId(source='manual') para que importar_estructura pueda "
        'aplicarle un YAML de curación exactamente igual que a una Obra '
        'importada de Jikan.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--slug', required=True)
        parser.add_argument('--titulo', required=True, help='Título base, SIN sufijo de tipo — se añade solo.')
        parser.add_argument('--tipo', default=Obra.TIPO_SERIE, choices=[t for t, _ in Obra.TIPO_CHOICES])
        parser.add_argument('--sinopsis', default='')
        parser.add_argument('--autor', default='')
        parser.add_argument('--fecha-publicacion', default=None, help='YYYY-MM-DD')
        parser.add_argument(
            '--categoria', action='append', default=[],
            help='Nombre de Categoria a asignar (repetible: --categoria X --categoria Y). '
                 'Se reutiliza si ya existe; se crea si no. Si entre ellas se pasa "Anime" y '
                 '--tipo es serie, el sufijo del título usa "(Anime)" en vez de "(Serie)".',
        )
        parser.add_argument(
            '--plural', action='store_true',
            help='Usa la forma plural del sufijo (p.ej. "(Libros)" en vez de "(Libro)") — '
                 'para Obras que agrupan varias unidades del tipo (una saga, una colección).',
        )
        parser.add_argument(
            '--sin-sufijo', action='store_true',
            help='No añade ningún sufijo al título — usa --titulo tal cual.',
        )

    def _titulo_con_sufijo(self, titulo, tipo, categorias, plural, sin_sufijo):
        if sin_sufijo:
            return titulo
        es_anime = tipo == Obra.TIPO_SERIE and any(c.strip().lower() in ETIQUETAS_ANIME for c in categorias)
        if es_anime:
            etiqueta = 'Anime'
        else:
            singular, plural_forma = SUFIJOS_TIPO.get(tipo, (None, None))
            if singular is None:
                return titulo
            etiqueta = plural_forma if plural else singular
        return f'{titulo} ({etiqueta})'

    def handle(self, *args, **options):
        slug = options['slug'] or slugify(options['titulo'])
        tipo = options['tipo']
        categorias_pedidas = options['categoria']

        titulo_final = self._titulo_con_sufijo(
            options['titulo'], tipo, categorias_pedidas, options['plural'], options['sin_sufijo'],
        )

        obra, creada = Obra.objects.get_or_create(
            slug=slug,
            defaults={
                'titulo': titulo_final,
                'tipo': tipo,
                'sinopsis': options['sinopsis'],
                'autor': options['autor'],
                'fecha_publicacion': options['fecha_publicacion'],
            },
        )
        externo, _ = ExternalId.objects.get_or_create(
            source=ExternalId.SOURCE_MANUAL, external_id=slug, obra=obra,
        )

        es_anime = tipo == Obra.TIPO_SERIE and any(c.strip().lower() in ETIQUETAS_ANIME for c in categorias_pedidas)
        nombres_categoria = set(categorias_pedidas)
        if not es_anime and tipo in CATEGORIA_AUTO_TIPO:
            nombres_categoria.add(CATEGORIA_AUTO_TIPO[tipo])

        for nombre in nombres_categoria:
            categoria, _ = Categoria.objects.get_or_create(nombre=nombre)
            obra.categorias.add(categoria)

        verbo = 'Creada' if creada else 'Ya existía'
        self.stdout.write(self.style.SUCCESS(f'{verbo}: {obra.titulo} (slug={slug})'))
        self.stdout.write(f'Categorías: {", ".join(sorted(nombres_categoria)) or "(ninguna)"}')