from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify

from core.validators import validate_image_size

from .catalogo import Obra, UnidadNarrativa

IMAGEN_VALIDATORS = [
    FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
    validate_image_size,
]


def personaje_image_path(instance, filename):
    return f'narrative/personajes/{slugify(instance.nombre)}/{filename}'


def etapa_image_path(instance, filename):
    return f'narrative/personajes/{slugify(instance.personaje.nombre)}/etapas/{filename}'


class Personaje(models.Model):
    """Hilo de personaje/entidad que cruza obras (ej. 'Tony Stark' en MCU
    Películas, Ironheart y What If...?). Puramente de descubrimiento: no
    participa en frontera_orden ni en ninguna regla de visibilidad -- cada
    unidad/post enlazado sigue bloqueado por su propia frontera (la de su
    obra, y obra_cruzada si la declara). A diferencia de TemaTransversal,
    no pertenece a una única Obra.

    unidades: solo apariciones confirmadas. Es lo único que leen las landings;
    las propuestas pendientes viven en PropuestaAparicion."""

    nombre = models.CharField(
        max_length=150, unique=True,
        help_text='Nombre en su primera aparición. Los que revelan algo después van como alias en sus etapas.',
    )
    wikidata_id = models.CharField(
        max_length=20, unique=True, null=True, blank=True,
        help_text='Identificador Q de Wikidata: une al mismo personaje entre obras sin depender del nombre.',
    )
    unidades = models.ManyToManyField(UnidadNarrativa, blank=True, related_name='personajes')
    imagen = models.ImageField(
        upload_to=personaje_image_path, blank=True, null=True, validators=IMAGEN_VALIDATORS,
        help_text='Imagen base: la de su primera aparición.',
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


class EtapaPersonaje(models.Model):
    """Cambio de nombre, aspecto o dato de un personaje. Solo se muestra cuando el
    lector ha terminado 'visible_tras' (criterio conservador: al acabar el arco,
    no al empezarlo). Los campos vacíos heredan de la etapa anterior."""

    personaje = models.ForeignKey(Personaje, on_delete=models.CASCADE, related_name='etapas')
    visible_tras = models.ForeignKey(
        UnidadNarrativa, on_delete=models.CASCADE, related_name='etapas_personaje',
        help_text='Unidad tras la que se revela el cambio. Elige el arco completo salvo que quieras precisar el episodio.',
    )
    alias = models.CharField(
        max_length=150, blank=True,
        help_text='Nombre con el que se le conoce desde esta etapa. En la web se muestra como su nombre, sin indicar que es un alias.',
    )
    nota = models.CharField(
        max_length=120, blank=True,
        help_text='Dato breve visible desde esta etapa (ej. «Recompensa: 30.000.000 ฿»).',
    )
    imagen = models.ImageField(upload_to=etapa_image_path, blank=True, null=True, validators=IMAGEN_VALIDATORS)

    class Meta:
        ordering = ['visible_tras__orden_fin']
        verbose_name = 'Etapa de personaje'
        verbose_name_plural = 'Etapas de personaje'
        constraints = [
            models.UniqueConstraint(fields=['personaje', 'visible_tras'], name='uniq_etapa_personaje_unidad'),
        ]

    def __str__(self):
        return f'{self.personaje} · tras {self.visible_tras}'


class RelevanciaPersonaje(models.Model):
    """Peso editorial de un personaje en una obra concreta (Loki: protagonista en su
    serie, secundario en Thor). Primer criterio del carrusel; sin fila = sin marcar."""

    NIVEL_SECUNDARIO = 1
    NIVEL_PRINCIPAL = 2
    NIVEL_PROTAGONISTA = 3
    NIVEL_CHOICES = [
        (NIVEL_PROTAGONISTA, 'Protagonista'),
        (NIVEL_PRINCIPAL, 'Principal'),
        (NIVEL_SECUNDARIO, 'Secundario'),
    ]

    personaje = models.ForeignKey(Personaje, on_delete=models.CASCADE, related_name='relevancias')
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='relevancias_personaje')
    nivel = models.PositiveSmallIntegerField(choices=NIVEL_CHOICES, default=NIVEL_PRINCIPAL)

    class Meta:
        ordering = ['obra', '-nivel', 'personaje__nombre']
        verbose_name = 'Relevancia de personaje'
        verbose_name_plural = 'Relevancias de personaje'
        constraints = [
            models.UniqueConstraint(fields=['personaje', 'obra'], name='uniq_relevancia_personaje_obra'),
        ]

    def __str__(self):
        return f'{self.personaje} en {self.obra}: {self.get_nivel_display()}'


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