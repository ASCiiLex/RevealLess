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
    no pertenece a una única Obra.

    unidades: solo apariciones confirmadas. Es lo único que leen las landings;
    las propuestas pendientes viven en PropuestaAparicion."""

    nombre = models.CharField(max_length=150, unique=True)
    wikidata_id = models.CharField(
        max_length=20, unique=True, null=True, blank=True,
        help_text='Identificador Q de Wikidata: une al mismo personaje entre obras sin depender del nombre.',
    )
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
        return '/static/img/default_personaje.jpg'


class PropuestaAparicion(models.Model):
    """Aparición de un personaje en una unidad, pendiente de revisión.
    Nunca es visible por sí misma: solo al aprobarse pasa a Personaje.unidades
    (asistente, no oráculo; mismo patrón que SolicitudTema)."""

    ORIGEN_WIKIDATA = 'wikidata'
    ORIGEN_IA = 'ia'
    ORIGEN_CHOICES = [
        (ORIGEN_WIKIDATA, 'Wikidata'),
        (ORIGEN_IA, 'IA (Haiku)'),
    ]

    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_APROBADA = 'aprobada'
    ESTADO_RECHAZADA = 'rechazada'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADA, 'Aprobada'),
        (ESTADO_RECHAZADA, 'Rechazada'),
    ]

    personaje = models.ForeignKey(Personaje, on_delete=models.CASCADE, related_name='propuestas')
    unidad = models.ForeignKey(UnidadNarrativa, on_delete=models.CASCADE, related_name='propuestas_personaje')
    origen = models.CharField(max_length=20, choices=ORIGEN_CHOICES)
    confianza = models.FloatField(null=True, blank=True)
    nota = models.CharField(max_length=300, blank=True, help_text='Justificación breve de la IA, si la hay.')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE)
    creado_en = models.DateTimeField(auto_now_add=True)
    resuelto_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Propuesta de aparición'
        verbose_name_plural = 'Propuestas de aparición'
        constraints = [
            models.UniqueConstraint(fields=['personaje', 'unidad'], name='uniq_propuesta_personaje_unidad'),
        ]

    def __str__(self):
        return f'{self.personaje} → {self.unidad} ({self.get_estado_display()})'