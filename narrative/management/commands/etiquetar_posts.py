from django.core.management.base import BaseCommand
from django.db import transaction

from narrative.services.etiquetado import etiquetar_personajes, personajes_en_post


class Command(BaseCommand):
    help = 'Etiqueta personajes en los posts existentes según su texto y su frontera.'

    def add_arguments(self, parser):
        parser.add_argument('--obra', help='Slug de la obra; por defecto, todas.')
        parser.add_argument('--dry-run', action='store_true', help='Muestra el resultado sin guardar.')

    def handle(self, *args, **opciones):
        from posts.models import Post  # posts depende de narrative

        posts = Post.objects.order_by('id')
        if opciones['obra']:
            posts = posts.filter(obra__slug=opciones['obra'])

        con_etiquetas = etiquetas = 0
        with transaction.atomic():
            for post in posts.iterator():
                ids = personajes_en_post(post) if opciones['dry_run'] else etiquetar_personajes(post)
                if ids:
                    con_etiquetas += 1
                    etiquetas += len(ids)
                    if opciones['dry_run']:
                        self.stdout.write(f'  post {post.id}: {sorted(ids)}')

        prefijo = '[dry-run] ' if opciones['dry_run'] else ''
        self.stdout.write(self.style.SUCCESS(
            f'{prefijo}{posts.count()} post(s) revisados, {con_etiquetas} con personajes, {etiquetas} etiqueta(s).'
        ))