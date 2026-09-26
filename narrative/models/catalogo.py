from django.core.validators import FileExtensionValidator
from django.db import models

from core.validators import validate_image_size

from .orden import recalcular_orden


def obra_image_path(instance, filename):
    return f'narrative/obras/{instance.slug}/{filename}'


def unidad_image_path(instance, filename):
    return f'narrative/unidades/{instance.obra.slug}/{filename}'


IMAGEN_VALIDATORS = [
    FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
    validate_image_size,
]


class Categoria(models.Model):
    """Etiqueta cosmética compartida entre obras (ej. 'anime', 'series',
    'películas', 'novelas'). Puramente de búsqueda/filtro — no participa
    en frontera_orden ni en ninguna regla de visibilidad, igual criterio
    que FamiliaNarrativa en posts/comments."""

    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre


class Obra(models.Model):
    TIPO_SERIE = 'serie'
    TIPO_PELICULA = 'pelicula'
    TIPO_ESPECIAL = 'especial'
    TIPO_OVA = 'ova'
    TIPO_CORTO = 'corto'
    TIPO_MANGA = 'manga'
    TIPO_LIBRO = 'libro'
    TIPO_CHOICES = [
        (TIPO_SERIE, 'Serie'),
        (TIPO_PELICULA, 'Película'),
        (TIPO_ESPECIAL, 'Especial de TV'),
        (TIPO_OVA, 'OVA'),
        (TIPO_CORTO, 'Corto'),
        (TIPO_MANGA, 'Manga'),
        (TIPO_LIBRO, 'Libro'),
    ]

    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_SERIE)
    sinopsis = models.TextField(blank=True)
    fecha_publicacion = models.DateField(null=True, blank=True)
    # Varios nombres separados por coma. Metadato cosmético, sin modelo Autor propio.
    autor = models.CharField(max_length=200, blank=True)
    imagen = models.ImageField(
        upload_to=obra_image_path,
        blank=True,
        null=True,
        validators=IMAGEN_VALIDATORS,
    )
    categorias = models.ManyToManyField(Categoria, blank=True, related_name='obras')

    # Vínculo informativo entre continuidades (ej. anime -> manga). No
    # participa en frontera_orden ni en visible_for(): cada continuidad
    # sigue siendo una isla de progreso independiente.
    adapta_a = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='adaptaciones',
        help_text='Obra origen si esta es una adaptación de otra continuidad (ej. anime → manga).',
    )

    class Meta:
        ordering = ['titulo']

    def __str__(self):
        return self.titulo

    @property
    def image_url(self):
        try:
            if self.imagen and hasattr(self.imagen, 'url'):
                return self.imagen.url
        except ValueError:
            pass
        return '/static/img/default_post.jpg'

    def obras_relacionadas(self):
        """Continuidades de la misma franquicia: la obra origen y sus
        adaptaciones. Sin mapeo de equivalencia entre escalas de orden."""
        relacionadas = []
        if self.adapta_a_id:
            relacionadas.append(self.adapta_a)
        relacionadas.extend(self.adaptaciones.all())
        return relacionadas

    def recalcular_orden(self):
        recalcular_orden(self)


class UnidadNarrativa(models.Model):
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='unidades')
    padre = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE, related_name='hijos'
    )
    tipo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=200)
    orden_local = models.PositiveIntegerField()
    # Real (Fase A, episodios vía Jikan) o aproximada (Fase B, por volumen).
    fecha = models.DateField(null=True, blank=True)
    imagen = models.ImageField(
        upload_to=unidad_image_path,
        blank=True,
        null=True,
        validators=IMAGEN_VALIDATORS,
    )

    orden_inicio = models.PositiveIntegerField(editable=False, default=0)
    orden_fin = models.PositiveIntegerField(editable=False, default=0)

    orden_manual = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['orden_inicio']

    def __str__(self):
        return f'{self.obra.titulo} · {self.nombre}'

    @property
    def es_hoja(self):
        return not self.hijos.exists()

    @property
    def etiqueta(self):
        return self.nombre

    @property
    def image_url(self):
        try:
            if self.imagen and hasattr(self.imagen, 'url'):
                return self.imagen.url
        except ValueError:
            pass
        return self.obra.image_url