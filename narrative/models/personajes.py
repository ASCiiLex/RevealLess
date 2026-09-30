from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify

from core.validators import validate_image_size

from .catalogo import UnidadNarrativa


def personaje_image_path(instance, filename):
    return f'narrative/personajes/{slugify(instance.nombre)}/{filename}'


class Personaje(models.Model):
    """Hilo de personaje/entidad que cruza obras (ej. 'Tony Stark' en MCU
    Películas, Ironheart y What If...?). Puramente de descubrimiento: no
    participa en frontera_orden ni en ninguna regla de visibilidad -- cada
    unidad/post enlazado sigue bloqueado por su propia frontera (la de su
    obra, y obra_cruzada si la declara). A diferencia de TemaTransversal,
    no pertenece a una única Obra."""

    nombre = models.CharField(max_length=150, unique=True)
    unidades = models.ManyToManyField(UnidadNarrativa, blank=True, related_name='personajes')
    imagen = models.ImageField(
        upload_to=personaje_image_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size,
        ],
    )

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Personaje'
        verbose_name_plural = 'Personajes'

    def __str__(self):
        return self.nombre

    @property
    def image_url(self):
        try:
            if self.imagen and hasattr(self.imagen, 'url'):
                return self.imagen.url
        except ValueError:
            pass
        return '/static/img/default_tema.jpg'