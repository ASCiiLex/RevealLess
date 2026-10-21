from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import User
from narrative.models import ClasificacionNarrativa
from core.imagenes.miniaturas import url_miniatura, url_variante
from core.validators import validate_image_size
from .managers import MODO_CRUCE_COMPARATIVA, MODO_CRUCE_MISMA_ESCENA, PostQuerySet


def post_image_path(instance, filename):
    return f'posts/{instance.author.username}/{filename}'


def post_galeria_path(instance, filename):
    return f'posts/{instance.post.author.username}/galeria/{filename}'


def misma_historia(a, b):
    """Adaptaciones directas o hermanas (mismo origen): cuentan las mismas escenas."""
    return (
        a.adapta_a_id == b.id
        or b.adapta_a_id == a.id
        or (a.adapta_a_id is not None and a.adapta_a_id == b.adapta_a_id)
    )


class Post(ClasificacionNarrativa, models.Model):
    objects = PostQuerySet.as_manager()

    DISPOSICION_AUTO = ''
    DISPOSICION_LADO = 'lado'
    DISPOSICION_APILADAS = 'apiladas'
    DISPOSICION_DESLIZADOR = 'deslizador'
    DISPOSICION_DESTACADA = 'destacada'
    DISPOSICION_FILA = 'fila'
    DISPOSICION_CUADRICULA = 'cuadricula'
    DISPOSICION_CHOICES = [
        (DISPOSICION_AUTO, 'Automática'),
        (DISPOSICION_LADO, 'Lado a lado'),
        (DISPOSICION_APILADAS, 'Apiladas'),
        (DISPOSICION_DESLIZADOR, 'Antes / después'),
        (DISPOSICION_DESTACADA, 'Una destacada'),
        (DISPOSICION_FILA, 'En fila'),
        (DISPOSICION_CUADRICULA, 'Cuadrícula'),
    ]
    # Disposiciones válidas según el número de imágenes de la galería.
    DISPOSICIONES_POR_NUMERO = {
        2: {DISPOSICION_LADO, DISPOSICION_APILADAS, DISPOSICION_DESLIZADOR},
        3: {DISPOSICION_DESTACADA, DISPOSICION_FILA},
        4: {DISPOSICION_CUADRICULA, DISPOSICION_DESTACADA},
    }
    MAX_IMAGENES = 4
    MIN_COMPARADOS = 2
    MAX_COMPARADOS = 4
    # Medidas que la optimización guarda al subir (core.imagenes.optimizacion).
    DIMENSIONES_IMAGEN = {'image': ('imagen_ancho', 'imagen_alto')}

    MODO_COMPARATIVA = MODO_CRUCE_COMPARATIVA
    MODO_MISMA_ESCENA = MODO_CRUCE_MISMA_ESCENA
    MODO_CRUCE_CHOICES = [
        (MODO_COMPARATIVA, 'Comparativa: ambas fronteras'),
        (MODO_MISMA_ESCENA, 'Misma escena: basta una frontera'),
    ]

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Autor',
    )
    obra = models.ForeignKey(
        'narrative.Obra',
        on_delete=models.PROTECT,
        related_name='posts',
        verbose_name='Obra',
    )
    # Opcional solo en posts: uno puede hablar de un tema sin anclarse a una parte.
    referencia_narrativa = models.ForeignKey(
        'narrative.UnidadNarrativa', on_delete=models.PROTECT, null=True, blank=True,
        related_name='%(class)s_referenciados', verbose_name='Referencia narrativa',
    )
    modo_cruce = models.CharField(
        max_length=20, choices=MODO_CRUCE_CHOICES, default=MODO_COMPARATIVA,
        verbose_name='Modo de cruce',
    )
    text = models.TextField(max_length=500, verbose_name='Texto')
    # Imagen única. Con 2 o más se usa la galería (PostImagen).
    image = models.ImageField(
        upload_to=post_image_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size,
        ],
        verbose_name='Imagen',
    )
    # Medidas visibles de la imagen única: la tarjeta reserva su proporción exacta antes de cargarla.
    imagen_ancho = models.PositiveIntegerField(null=True, blank=True, editable=False, verbose_name='Ancho de la imagen')
    imagen_alto = models.PositiveIntegerField(null=True, blank=True, editable=False, verbose_name='Alto de la imagen')
    disposicion = models.CharField(
        max_length=20, choices=DISPOSICION_CHOICES, blank=True, default=DISPOSICION_AUTO,
        verbose_name='Disposición de la galería',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')

    is_processed = models.BooleanField(default=False, verbose_name='Hashtags procesados')

    temas_transversales = models.ManyToManyField(
        'narrative.TemaTransversal',
        blank=True,
        related_name='posts',
        verbose_name='Temas transversales',
    )

    personajes = models.ManyToManyField(
        'narrative.Personaje',
        blank=True,
        related_name='posts',
        verbose_name='Personajes',
    )

    # «X vs Z»: elegidos por el autor, con orden. También se vuelcan en `personajes`.
    personajes_comparados = models.ManyToManyField(
        'narrative.Personaje',
        through='PersonajeComparado',
        blank=True,
        related_name='posts_comparados',
        verbose_name='Personajes comparados',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Publicación'
        verbose_name_plural = 'Publicaciones'
        constraints = [
            models.CheckConstraint(
                check=~models.Q(frontera_origen=ClasificacionNarrativa.ORIGEN_HEREDADO_POST),
                name='post_frontera_origen_no_heredado',
            ),
            models.CheckConstraint(
                check=models.Q(frontera_spoiler__isnull=False),
                name='post_frontera_spoiler_obligatoria',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(obra_cruzada__isnull=True, frontera_cruzada__isnull=True)
                    | (models.Q(obra_cruzada__isnull=False) & models.Q(frontera_cruzada__isnull=False))
                ),
                name='post_frontera_cruzada_consistency',
            ),
        ]

    def __str__(self):
        return f'Post de {self.author.username} ({self.created_at.date()})'

    def clean(self):
        super().clean()
        if self.referencia_narrativa_id and self.referencia_narrativa.obra_id != self.obra_id:
            raise ValidationError({'referencia_narrativa': 'Debe pertenecer a la obra del post.'})
        if self.frontera_spoiler_id and self.frontera_spoiler.obra_id != self.obra_id:
            raise ValidationError({'frontera_spoiler': 'Debe pertenecer a la obra del post.'})
        if self.obra_cruzada_id:
            if self.obra_cruzada_id == self.obra_id:
                raise ValidationError({'obra_cruzada': 'Debe ser una obra distinta a la del post.'})
            if self.frontera_cruzada_id and self.frontera_cruzada.obra_id != self.obra_cruzada_id:
                raise ValidationError({'frontera_cruzada': 'Debe pertenecer a obra_cruzada.'})
            if self.modo_cruce == self.MODO_MISMA_ESCENA and not misma_historia(self.obra, self.obra_cruzada):
                raise ValidationError({'modo_cruce': 'La misma escena solo vale entre adaptaciones de una historia.'})

    @property
    def likes_count(self):
        if hasattr(self, "likes_total"):
            return self.likes_total
        from likes.models import PostReaction
        return PostReaction.objects.filter(post=self).count()

    @property
    def comments_count(self):
        if hasattr(self, "comments_total"):
            return self.comments_total
        return self.comments.count()

    @property
    def username_tag(self):
        return f"@{self.author.username}"

    @property
    def image_url(self):
        """None si el post no tiene foto: es opcional y no se sustituye por una genérica."""
        try:
            if self.image and hasattr(self.image, "url"):
                return self.image.url
        except ValueError:
            pass
        return None

    @property
    def miniatura_url(self):
        return url_miniatura(self.image)

    @property
    def media_url(self):
        return url_variante(self.image, 'med')

    def imagenes_para_mostrar(self, variante=None):
        """Lista única para pintar: la galería con su encuadre si existe; si no, la imagen simple.
        variante: None (original), 'med' (feed y detalle) o 'min' (teselas de perfil y guardados).
        Al listar posts conviene prefetch_related('imagenes')."""
        def url(archivo, original):
            return url_variante(archivo, variante) if variante else original

        galeria = [
            {
                'url': url(i.imagen, i.image_url), 'etiqueta': i.etiqueta,
                'enfoque_x': i.enfoque_x, 'enfoque_y': i.enfoque_y, 'zoom': i.zoom,
            }
            for i in self.imagenes.all() if i.image_url
        ]
        if galeria or not self.image_url:
            return galeria
        return [{
            'url': url(self.image, self.image_url), 'etiqueta': '',
            'enfoque_x': PostImagen.ENFOQUE_CENTRO, 'enfoque_y': PostImagen.ENFOQUE_CENTRO,
            'zoom': PostImagen.ZOOM_BASE,
        }]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.is_processed:
            from notifications.utils import extract_hashtags

            tags = extract_hashtags(self.text)

            for tag in tags:
                hashtag, _ = Hashtag.objects.get_or_create(name=tag)
                PostHashtag.objects.get_or_create(
                    post=self,
                    hashtag=hashtag
                )

            self.is_processed = True
            super().save(update_fields=['is_processed'])


class PostImagen(models.Model):
    """Imagen de una galería (2 a 4 por post). La etiqueta se muestra sobre ella (ej. «Anime»).
    El encuadre (punto de enfoque y zoom) se aplica al mostrarla: el original no se recorta."""

    ENFOQUE_CENTRO = 50
    ZOOM_BASE = 100
    ZOOM_MAXIMO = 300

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='imagenes', verbose_name='Publicación')
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


class PersonajeComparado(models.Model):
    """Personaje de un «X vs Z». Sin personaje aún si está propuesto (solicitud pendiente)."""

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comparaciones', verbose_name='Publicación',
    )
    personaje = models.ForeignKey(
        'narrative.Personaje', on_delete=models.CASCADE, null=True, blank=True, related_name='comparaciones',
        verbose_name='Personaje',
    )
    solicitud = models.ForeignKey(
        'narrative.SolicitudPersonaje', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='comparaciones', verbose_name='Solicitud',
    )
    orden = models.PositiveSmallIntegerField(default=0, verbose_name='Orden')

    class Meta:
        ordering = ['orden']
        verbose_name = 'Personaje comparado'
        verbose_name_plural = 'Personajes comparados'
        constraints = [
            models.UniqueConstraint(fields=['post', 'personaje'], name='uniq_personaje_comparado_post'),
        ]

    def __str__(self):
        return f'{self.post_id} · {self.personaje or self.solicitud}'


class Hashtag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Nombre')

    class Meta:
        ordering = ['name']
        verbose_name = 'Hashtag'
        verbose_name_plural = 'Hashtags'

    def __str__(self):
        return f"#{self.name}"


class PostHashtag(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="post_hashtags",
        verbose_name='Publicación',
    )
    hashtag = models.ForeignKey(
        Hashtag,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name='Hashtag',
    )

    class Meta:
        unique_together = ('post', 'hashtag')
        verbose_name = 'Hashtag de publicación'
        verbose_name_plural = 'Hashtags de publicación'

    def __str__(self):
        return f"{self.post.id} - #{self.hashtag.name}"