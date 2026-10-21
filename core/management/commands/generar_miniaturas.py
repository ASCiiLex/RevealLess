from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Q

from core.imagenes.miniaturas import guardar_miniatura, nombre_miniatura
from core.imagenes.optimizacion import campos_imagen


class Command(BaseCommand):
    help = 'Crea las miniaturas que faltan de las imágenes ya guardadas. Se puede repetir sin riesgo.'

    def handle(self, *args, **opciones):
        creadas = existentes = errores = 0
        for modelo in apps.get_models():
            for campo in campos_imagen(modelo):
                nombres = (
                    modelo.objects.exclude(Q(**{campo.name: ''}) | Q(**{f'{campo.name}__isnull': True}))
                    .order_by().values_list(campo.name, flat=True).distinct()
                )
                for nombre in nombres:
                    if campo.storage.exists(nombre_miniatura(nombre)):
                        existentes += 1
                        continue
                    try:
                        with campo.storage.open(nombre, 'rb') as archivo:
                            datos = archivo.read()
                    except OSError as exc:
                        errores += 1
                        self.stderr.write(f'No se puede leer {nombre}: {exc}')
                        continue
                    if guardar_miniatura(campo.storage, nombre, datos):
                        creadas += 1
                        self.stdout.write(f'{nombre} -> {nombre_miniatura(nombre)}')
                    else:
                        errores += 1

        self.stdout.write(self.style.SUCCESS(
            f'{creadas} creadas, {existentes} ya existían, {errores} con error.'
        ))