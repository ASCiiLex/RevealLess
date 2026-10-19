from django.apps import apps
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db.models import Q

from core.imagenes import campos_imagen, optimizar_imagen


class Command(BaseCommand):
    help = 'Optimiza las imágenes ya guardadas (lado máximo, recompresión y sin EXIF) conservando su nombre.'

    def add_arguments(self, parser):
        parser.add_argument('--aplicar', action='store_true', help='Sin esta opción solo informa (simulación).')

    def handle(self, *args, aplicar=False, **opciones):
        cuantas, antes, despues = 0, 0, 0
        for modelo in apps.get_models():
            for campo in campos_imagen(modelo):
                nombres = (
                    modelo.objects.exclude(Q(**{campo.name: ''}) | Q(**{f'{campo.name}__isnull': True}))
                    .order_by().values_list(campo.name, flat=True).distinct()
                )
                for nombre in nombres:
                    try:
                        with campo.storage.open(nombre, 'rb') as archivo:
                            datos = archivo.read()
                    except OSError as exc:
                        self.stderr.write(f'No se puede leer {nombre}: {exc}')
                        continue
                    optimizada = optimizar_imagen(datos)
                    if optimizada is None:
                        continue

                    cuantas += 1
                    antes += len(datos)
                    despues += len(optimizada)
                    self.stdout.write(f'{nombre}: {len(datos) // 1024} KB -> {len(optimizada) // 1024} KB')
                    if aplicar:
                        campo.storage.delete(nombre)
                        guardado = campo.storage.save(nombre, ContentFile(optimizada))
                        # Si el almacenamiento asignara otro nombre, la BD se actualiza para no perder la imagen.
                        if guardado != nombre:
                            modelo.objects.filter(**{campo.name: nombre}).update(**{campo.name: guardado})

        self.stdout.write(self.style.SUCCESS(
            f'{cuantas} imágenes: {antes / 1048576:.1f} MB -> {despues / 1048576:.1f} MB'
        ))
        if not aplicar:
            self.stdout.write('Simulación: añade --aplicar para guardar los cambios.')