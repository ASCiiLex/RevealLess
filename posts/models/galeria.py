from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from core.imagenes.miniaturas import url_miniatura
from core.validators import validate_image_size


def post_galeria_path(instance, filename):
    return f'posts/{instance.post.author.username}/galeria/{filename}'


class PostImagen(models.Model):
    """Imagen de una galería (2 a 4 por post). La etiqueta se muestra sobre ella (ej. «Anime»).
    El encuadre (punto de enfoque y zoom) se aplica al mostrarla: el original no se recorta."""

    ENFOQUE_CENTRO = 50
    ZOOM_BASE = 100
    ZOOM_MAXIMO = 300

    post = models.ForeignKey(
        'posts.Post', on_delete=models.CASCADE, related_name='imagenes', verbose_name='Publicación',
    )
    imagen = models.ImageField(
        upload_to=post_galeria_path,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size,
        ],
        verbose_name='Imagen',
    )
    etiqueta = models.CharField(max_length=40, blank=True, verbose_name='Etiqueta')
    orden = models.PositiveSmallIntegerField(default=0, verbose_name='Orden')
    # Porcentajes: 0 = borde izquierdo/superior, 100 = derecho/inferior.
    enfoque_x = models.PositiveSmallIntegerField(
        default=ENFOQUE_CENTRO, validators=[MaxValueValidator(100)], verbose_name='Enfoque horizontal (%)',
    )
    enfoque_y = models.PositiveSmallIntegerField(
        default=ENFOQUE_CENTRO, validators=[MaxValueValidator(100)], verbose_name='Enfoque vertical (%)',
    )
    zoom = models.PositiveSmallIntegerField(
        default=ZOOM_BASE, validators=[MinValueValidator(ZOOM_BASE), MaxValueValidator(ZOOM_MAXIMO)],
        verbose_name='Zoom (%)',
    )

    class Meta:
        ordering = ['orden']
        verbose_name = 'Imagen de publicación'
        verbose_name_plural = 'Imágenes de publicación'

    def __str__(self):
        return f'{self.post_id} · imagen {self.orden + 1}'

    @property
    def image_url(self):
        try:
            if self.imagen and hasattr(self.imagen, 'url'):
                return self.imagen.url
        except ValueError:
            pass
        return None

    @property
    def miniatura_url(self):
        return url_miniatura(self.imagen)