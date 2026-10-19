from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Case, F, Q, Value, When
from django.db.models.functions import Greatest

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
    """Etiqueta compartida entre obras (ej. 'anime', 'películas'). No participa
    en frontera_orden ni en visibilidad. Si es_universo, agrupa una franquicia
    (ej. 'Tierra Media', 'Star Wars') y sus obras se muestran como relacionadas."""

    nombre = models.CharField(max_length=50, unique=True, verbose_name='Nombre')
    es_universo = models.BooleanField(
        default=False,
        verbose_name='Es un universo',
        help_text='Las obras de esta categoría se muestran como relacionadas entre sí.',
    )

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

    # Portada por defecto según el tipo; especiales, OVAs y cortos comparten la de serie.
    IMAGEN_POR_DEFECTO = {
        TIPO_PELICULA: '/static/img/default_pelicula.jpg',
        TIPO_MANGA: '/static/img/default_manga.jpg',
        TIPO_LIBRO: '/static/img/default_libro.jpg',
    }
    IMAGEN_POR_DEFECTO_GENERICA = '/static/img/default_serie.jpg'

    titulo = models.CharField(max_length=200, verbose_name='Título')
    slug = models.SlugField(unique=True, verbose_name='Slug')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_SERIE, verbose_name='Tipo')
    sinopsis = models.TextField(blank=True, verbose_name='Sinopsis')
    fecha_publicacion = models.DateField(null=True, blank=True, verbose_name='Fecha de publicación')
    # Varios nombres separados por coma. Metadato cosmético, sin modelo Autor propio.
    autor = models.CharField(max_length=200, blank=True, verbose_name='Autor')
    imagen = models.ImageField(
        upload_to=obra_image_path,
        blank=True,
        null=True,
        validators=IMAGEN_VALIDATORS,
        verbose_name='Portada',
    )
    categorias = models.ManyToManyField(Categoria, blank=True, related_name='obras', verbose_name='Categorías')

    # Vínculo informativo entre continuidades (ej. anime -> manga). No
    # participa en frontera_orden ni en visible_for(): cada continuidad
    # sigue siendo una isla de progreso independiente.
    adapta_a = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='adaptaciones',
        verbose_name='Adaptación de',
        help_text='Obra origen si esta es una adaptación de otra continuidad (ej. anime → manga).',
    )
    traducido = models.BooleanField(
        default=False,
        verbose_name='Traducido',
        help_text='Sinopsis ya traducida al español por traducir_catalogo.',
    )

    class Meta:
        ordering = ['titulo']
        verbose_name = 'Obra'
        verbose_name_plural = 'Obras'

    def __str__(self):
        return self.titulo

    @property
    def image_url(self):
        try:
            if self.imagen and hasattr(self.imagen, 'url'):
                return self.imagen.url
        except ValueError:
            pass
        return self.IMAGEN_POR_DEFECTO.get(self.tipo, self.IMAGEN_POR_DEFECTO_GENERICA)

    def obras_relacionadas(self):
        """Origen, adaptaciones, hermanas (otras adaptaciones del mismo origen)
        y obras que comparten una categoría universo. Solo informativo."""
        filtro = Q(adapta_a=self) | Q(
            categorias__in=self.categorias.filter(es_universo=True)
        )
        if self.adapta_a_id:
            filtro |= Q(id=self.adapta_a_id) | Q(adapta_a_id=self.adapta_a_id)
        return Obra.objects.filter(filtro).exclude(id=self.id).distinct()

    def recalcular_orden(self):
        recalcular_orden(self)
        # Diferidos: clasificacion y progreso importan este módulo.
        from .clasificacion import refrescar_fronteras
        from .progreso import refrescar_progresos
        refrescar_fronteras(self)
        refrescar_progresos(self)


class UnidadNarrativa(models.Model):
    # Entrega anunciada y aún no estrenada: se lee justo antes de ella.
    TIPO_PREVIO = 'previo'

    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='unidades', verbose_name='Obra')
    padre = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE, related_name='hijos',
        verbose_name='Unidad padre',
    )
    tipo = models.CharField(max_length=50, verbose_name='Tipo')
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    orden_local = models.PositiveIntegerField(verbose_name='Orden local')
    # Real (Fase A, episodios vía Jikan) o aproximada (Fase B, por volumen).
    fecha = models.DateField(null=True, blank=True, verbose_name='Fecha')
    imagen = models.ImageField(
        upload_to=unidad_image_path,
        blank=True,
        null=True,
        validators=IMAGEN_VALIDATORS,
        verbose_name='Imagen',
    )

    orden_inicio = models.PositiveIntegerField(editable=False, default=0, verbose_name='Inicio en la obra')
    orden_fin = models.PositiveIntegerField(editable=False, default=0, verbose_name='Fin en la obra')

    orden_manual = models.PositiveIntegerField(null=True, blank=True, verbose_name='Orden manual')
    traducido = models.BooleanField(
        default=False,
        verbose_name='Traducido',
        help_text='Nombre ya traducido al español por traducir_catalogo.',
    )

    class Meta:
        ordering = ['orden_inicio']
        verbose_name = 'Unidad narrativa'
        verbose_name_plural = 'Unidades narrativas'

    def __str__(self):
        # El contenedor distingue nombres repetidos («Episodio 1» de Naruto y de Shippūden).
        # Quien liste muchas unidades debe hacer select_related('obra', 'padre').
        if self.padre_id:
            return f'{self.obra.titulo} · {self.padre.nombre} · {self.nombre}'
        return f'{self.obra.titulo} · {self.nombre}'

    @property
    def es_hoja(self):
        return not self.hijos.exists()

    @property
    def es_previa(self):
        return self.tipo == self.TIPO_PREVIO

    @property
    def orden_frontera(self):
        """Posición que exige como frontera. El previo, la anterior a él:
        0 en una obra nueva, el final de la entrega anterior en una continuación."""
        if self.es_previa:
            return max(self.orden_inicio - 1, 0)
        return self.orden_fin

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


def expresion_orden_frontera():
    """Equivalente SQL de UnidadNarrativa.orden_frontera, para recalcular en bloque."""
    return Case(
        When(
            tipo=UnidadNarrativa.TIPO_PREVIO,
            then=Greatest(F('orden_inicio') - 1, Value(0), output_field=models.IntegerField()),
        ),
        default=F('orden_fin'),
        output_field=models.IntegerField(),
    )