from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Q

from core.imagenes.miniaturas import VARIANTES, guardar_variantes, nombre_variante
from core.imagenes.optimizacion import campos_imagen


class Command(BaseCommand):
    help = 'Crea las variantes reducidas (min, med) que falten de las imágenes guardadas. Se puede repetir sin riesgo.'

    def handle(self, *args, **opciones):
        creadas = completas = errores = 0
        for modelo in apps.get_models():
            for campo in campos_imagen(modelo):
                nombres = (
                    modelo.objects.exclude(Q(**{campo.name: ''}) | Q(**{f'{campo.name}__isnull': True}))
                    .order_by().values_list(campo.name, flat=True).distinct()
                )
                for nombre in nombres:
                    faltan = [v for v in VARIANTES if not campo.storage.exists(nombre_variante(nombre, v))]
                    if not faltan:
                        completas += 1
                        continue
                    try:
                        with campo.storage.open(nombre, 'rb') as archivo:
                            datos = archivo.read()
                    except OSError as exc:
                        errores += 1
                        self.stderr.write(f'No se puede leer {nombre}: {exc}')
                        continue
                    if guardar_variantes(campo.storage, nombre, datos, faltan):
                        creadas += len(faltan)
                        self.stdout.write(f'{nombre} -> {", ".join(faltan)}')
                    else:
                        errores += 1

        self.stdout.write(self.style.SUCCESS(
            f'{creadas} variantes creadas, {completas} imágenes ya completas, {errores} con error.'
        ))