from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from django.db.models.signals import post_save, pre_save
        from .imagenes.optimizacion import miniaturas_al_guardar, optimizar_al_guardar

        # Un único punto para todas las imágenes de todos los modelos (posts, galerías, avatares, catálogo).
        pre_save.connect(optimizar_al_guardar, dispatch_uid='core_optimizar_imagenes')
        post_save.connect(miniaturas_al_guardar, dispatch_uid='core_miniaturas_imagenes')