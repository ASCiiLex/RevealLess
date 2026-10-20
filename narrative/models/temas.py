from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import F, IntegerField, Min, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce

from core.validators import validate_image_size

from .catalogo import Obra, UnidadNarrativa
from .progreso import ProgresoUsuario


def tema_image_path(instance, filename):
    return f'narrative/temas/{instance.obra.slug}/{filename}'


class TemaQuerySet(models.QuerySet):
    def visibles_para(self, user):
        """Temáticos sin unidades, o minihistorias cuya primera unidad ya alcanzó el lector:
        el nombre de una minihistoria futura ya es un spoiler."""
        progreso = ProgresoUsuario.objects.filter(
            usuario=user, obra=OuterRef('obra'),
        ).values('orden_absoluto')[:1]
        return self.annotate(
            primera_unidad=Min('unidades__orden_fin'),
            progreso_lector=Coalesce(Subquery(progreso, output_field=IntegerField()), Value(-1)),
        ).filter(Q(primera_unidad__isnull=True) | Q(primera_unidad__lte=F('progreso_lector')))


class TemaTransversal(models.Model):
    """Hilo temático de una obra sin anclarse a una unidad concreta (ej.
    'Frutas del diablo'), o minihistoria publicada dentro de capítulos
    existentes. Etiqueta de agrupación y suscripción: no participa en
    frontera_orden. Vive en narrative porque es propiedad de la obra."""

    objects = TemaQuerySet.as_manager()

    TIPO_TEMATICO = 'tematico'
    TIPO_MINIHISTORIA = 'minihistoria'
    TIPO_CHOICES = [
        (TIPO_TEMATICO, 'Temático'),
        (TIPO_MINIHISTORIA, 'Minihistoria'),
    ]

    obra = models.ForeignKey(
        Obra, on_delete=models.CASCADE, related_name='temas_transversales', verbose_name='Obra',
    )
    nombre = models.CharField(max_length=150, verbose_name='Nombre')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_TEMATICO, verbose_name='Tipo')
    # Solo minihistorias: unidades donde aparece. No implica pertenencia narrativa.
    unidades = models.ManyToManyField(
        UnidadNarrativa, blank=True, related_name='temas_transversales', verbose_name='Unidades',
    )
    # Imagen propia del tema, deliberadamente distinta a la de su obra --
    # para no confundir un "lomo de tema" con un lomo de obra real en el
    # carrusel. Sin imagen propia -> icono generico via image_url.
    imagen = models.ImageField(
        upload_to=tema_image_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size,
        ],
        verbose_name='Imagen',
    )

    class Meta:
        unique_together = ('obra', 'nombre')
        ordering = ['nombre']
        verbose_name = 'Tema transversal'
        verbose_name_plural = 'Temas transversales'

    def __str__(self):
        return f'{self.obra.titulo} · {self.nombre}'

    @property
    def image_url(self):
        try:
            if self.imagen and hasattr(self.imagen, 'url'):
                return self.imagen.url
        except ValueError:
            pass
        return '/static/img/default_tema.jpg'


class SolicitudTema(models.Model):
    """Propuesta de usuario para un TemaTransversal nuevo. Solo se crea el
    tema tras aprobación explícita desde admin."""

    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_APROBADA = 'aprobada'
    ESTADO_RECHAZADA = 'rechazada'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADA, 'Aprobada'),
        (ESTADO_RECHAZADA, 'Rechazada'),
    ]

    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='solicitudes_tema', verbose_name='Obra')
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='solicitudes_tema', verbose_name='Usuario',
    )
    nombre = models.CharField(max_length=150, verbose_name='Nombre')
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE, verbose_name='Estado',
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    resuelto_en = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de resolución')

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Solicitud de tema'
        verbose_name_plural = 'Solicitudes de tema'

    def __str__(self):
        return f'{self.usuario.username} propone "{self.nombre}" en {self.obra.titulo} ({self.estado})'