from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
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

    unidades: solo apariciones confirmadas. Es lo único que leen las landings.
    Se escribe siempre a través de PropuestaAparicion (aprobar, rechazar, mover),
    para que cada aparición tenga origen y estado.

    identidad_de: otra identidad con ficha propia (Sogeking → Usopp, Tobi → Obito).
    Cada una conserva su ficha y su feed; la principal suma los de la otra solo
    cuando el lector ya conoce el vínculo (identidad_revelada_tras)."""

    nombre = models.CharField(
        max_length=150, unique=True, verbose_name='Nombre',
        help_text='Nombre en su primera aparición. Los que revelan algo después van como alias en sus etapas.',
    )
    wikidata_id = models.CharField(
        max_length=20, unique=True, null=True, blank=True, verbose_name='ID de Wikidata',
        help_text='Identificador Q de Wikidata: une al mismo personaje entre obras sin depender del nombre.',
    )
    unidades = models.ManyToManyField(
        UnidadNarrativa, blank=True, related_name='personajes', verbose_name='Apariciones',
    )
    imagen = models.ImageField(
        upload_to=personaje_image_path, blank=True, null=True, validators=IMAGEN_VALIDATORS,
        verbose_name='Imagen',
        help_text='Imagen base: la de su primera aparición.',
    )
    identidad_de = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='otras_identidades',
        verbose_name='Es otra identidad de',
        help_text='Disfraz o identidad con ficha propia (ej. Sogeking → Usopp). Cada uno mantiene su ficha y su feed.',
    )
    identidad_revelada_tras = models.ManyToManyField(
        UnidadNarrativa, blank=True, related_name='identidades_reveladas',
        verbose_name='Se sabe desde',
        help_text='Unidades tras las que se conoce el vínculo (una por obra si hace falta). Vacío: desde su primera aparición.',
    )

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Personaje'
        verbose_name_plural = 'Personajes'

    def __str__(self):
        return self.nombre

    def clean(self):
        super().clean()
        if self.identidad_de_id:
            if self.identidad_de_id == self.pk:
                raise ValidationError({'identidad_de': 'No puede ser otra identidad de sí mismo.'})
            if self.identidad_de.identidad_de_id:
                raise ValidationError({'identidad_de': 'Elige la identidad principal: no se encadenan identidades.'})

    @property
    def image_url(self):
        try:
            if self.imagen and hasattr(self.imagen, 'url'):
                return self.imagen.url
        except ValueError:
            pass
        return '/static/img/default_personaje.jpg'


class RelevanciaPersonaje(models.Model):
    """Peso editorial de un personaje en una obra concreta (Loki: protagonista en su
    serie, secundario en Thor). Primer criterio del carrusel. Sin fila cuenta como
    Secundario: solo se marcan las excepciones hacia arriba o hacia abajo.
    Una etapa superada con nivel lo sustituye. Valores espaciados para poder
    intercalar niveles sin renumerar."""

    NIVEL_EPISODICO = 10
    NIVEL_SECUNDARIO = 20
    NIVEL_DESTACADO = 30
    NIVEL_PRINCIPAL = 40
    NIVEL_PROTAGONISTA = 50
    NIVEL_SIN_MARCAR = NIVEL_SECUNDARIO
    # Niveles que el carrusel muestra de entrada.
    NIVEL_MINIMO_POR_DEFECTO = NIVEL_PRINCIPAL
    NIVEL_CHOICES = [
        (NIVEL_PROTAGONISTA, 'Protagonista'),
        (NIVEL_PRINCIPAL, 'Principal'),
        (NIVEL_DESTACADO, 'Destacado'),
        (NIVEL_SECUNDARIO, 'Secundario'),
        (NIVEL_EPISODICO, 'Episódico'),
    ]

    personaje = models.ForeignKey(
        Personaje, on_delete=models.CASCADE, related_name='relevancias', verbose_name='Personaje',
    )
    obra = models.ForeignKey(
        Obra, on_delete=models.CASCADE, related_name='relevancias_personaje', verbose_name='Obra',
    )
    nivel = models.PositiveSmallIntegerField(choices=NIVEL_CHOICES, default=NIVEL_PRINCIPAL, verbose_name='Nivel')

    class Meta:
        ordering = ['obra', '-nivel', 'personaje__nombre']
        verbose_name = 'Relevancia de personaje'
        verbose_name_plural = 'Relevancias de personaje'
        constraints = [
            models.UniqueConstraint(fields=['personaje', 'obra'], name='uniq_relevancia_personaje_obra'),
        ]

    def __str__(self):
        return f'{self.personaje} en {self.obra}: {self.get_nivel_display()}'


class EtapaPersonaje(models.Model):
    """Cambio de nombre, aspecto, dato o relevancia de un personaje. Solo se aplica
    cuando el lector ha terminado 'visible_tras' (criterio conservador: al acabar el
    arco, no al empezarlo). Los campos vacíos heredan de la etapa anterior."""

    personaje = models.ForeignKey(
        Personaje, on_delete=models.CASCADE, related_name='etapas', verbose_name='Personaje',
    )
    visible_tras = models.ForeignKey(
        UnidadNarrativa, on_delete=models.CASCADE, related_name='etapas_personaje',
        verbose_name='Visible tras',
        help_text='Unidad tras la que se revela el cambio. Elige el arco completo salvo que quieras precisar el episodio.',
    )
    alias = models.CharField(
        max_length=150, blank=True, verbose_name='Alias',
        help_text='Nombre con el que se le conoce desde esta etapa. En la web se muestra como su nombre, sin indicar que es un alias.',
    )
    nota = models.CharField(
        max_length=120, blank=True, verbose_name='Nota',
        help_text='Dato breve visible desde esta etapa (ej. «Recompensa: 30.000.000 ฿»).',
    )
    nivel = models.PositiveSmallIntegerField(
        choices=RelevanciaPersonaje.NIVEL_CHOICES, null=True, blank=True, verbose_name='Nivel',
        help_text='Relevancia en esta obra desde esta etapa (ej. de Secundario a Principal al unirse). Vacío: no cambia.',
    )
    imagen = models.ImageField(
        upload_to=etapa_image_path, blank=True, null=True, validators=IMAGEN_VALIDATORS, verbose_name='Imagen',
    )

    class Meta:
        ordering = ['visible_tras__orden_fin']
        verbose_name = 'Etapa de personaje'
        verbose_name_plural = 'Etapas de personaje'
        constraints = [
            models.UniqueConstraint(fields=['personaje', 'visible_tras'], name='uniq_etapa_personaje_unidad'),
        ]

    def __str__(self):
        return f'{self.personaje} · tras {self.visible_tras}'


class PropuestaAparicion(models.Model):
    """Aparición de un personaje en una unidad. Solo la aprobada pasa a Personaje.unidades
    y es visible (asistente, no oráculo; mismo patrón que SolicitudTema).
    Las añadidas a mano desde el admin entran con origen Manual."""

    ORIGEN_WIKIDATA = 'wikidata'
    ORIGEN_IA = 'ia'
    ORIGEN_MANUAL = 'manual'
    ORIGEN_CHOICES = [
        (ORIGEN_WIKIDATA, 'Wikidata'),
        (ORIGEN_IA, 'IA (Haiku)'),
        (ORIGEN_MANUAL, 'Manual'),
    ]

    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_APROBADA = 'aprobada'
    ESTADO_RECHAZADA = 'rechazada'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADA, 'Aprobada'),
        (ESTADO_RECHAZADA, 'Rechazada'),
    ]

    personaje = models.ForeignKey(
        Personaje, on_delete=models.CASCADE, related_name='propuestas', verbose_name='Personaje',
    )
    unidad = models.ForeignKey(
        UnidadNarrativa, on_delete=models.CASCADE, related_name='propuestas_personaje',
        verbose_name='Unidad narrativa',
    )
    origen = models.CharField(max_length=20, choices=ORIGEN_CHOICES, default=ORIGEN_MANUAL, verbose_name='Origen')
    confianza = models.FloatField(null=True, blank=True, verbose_name='Confianza')
    nota = models.CharField(
        max_length=300, blank=True, verbose_name='Nota', help_text='Justificación breve de la IA, si la hay.',
    )
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE, verbose_name='Estado',
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    resuelto_en = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de resolución')

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Propuesta de aparición'
        verbose_name_plural = 'Propuestas de aparición'
        constraints = [
            models.UniqueConstraint(fields=['personaje', 'unidad'], name='uniq_propuesta_personaje_unidad'),
        ]

    def __str__(self):
        return f'{self.personaje} → {self.unidad} ({self.get_estado_display()})'


class SolicitudPersonaje(models.Model):
    """Personaje propuesto por un usuario al publicar una comparativa. Al aprobarla se crea
    (o reutiliza) el personaje, se aprueba su aparición en 'unidad' y se vincula a los posts
    que lo propusieron. Mismo patrón que SolicitudTema."""

    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_APROBADA = 'aprobada'
    ESTADO_RECHAZADA = 'rechazada'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADA, 'Aprobada'),
        (ESTADO_RECHAZADA, 'Rechazada'),
    ]

    obra = models.ForeignKey(
        Obra, on_delete=models.CASCADE, related_name='solicitudes_personaje', verbose_name='Obra',
    )
    unidad = models.ForeignKey(
        UnidadNarrativa, on_delete=models.CASCADE, related_name='solicitudes_personaje',
        verbose_name='Primera aparición',
        help_text='Se propone la frontera del post: corrígela antes de aprobar si hace falta.',
    )
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='solicitudes_personaje', verbose_name='Usuario',
    )
    nombre = models.CharField(max_length=150, verbose_name='Nombre')
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE, verbose_name='Estado',
    )
    personaje = models.ForeignKey(
        Personaje, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes',
        verbose_name='Personaje',
        help_text='Vacío: se crea al aprobar (o se reutiliza uno con el mismo nombre). Elige uno si es el mismo con otro nombre.',
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    resuelto_en = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de resolución')

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Solicitud de personaje'
        verbose_name_plural = 'Solicitudes de personaje'

    def __str__(self):
        return f'{self.usuario.username} propone «{self.nombre}» en {self.obra.titulo} ({self.estado})'

    def clean(self):
        super().clean()
        if self.unidad_id and self.obra_id and self.unidad.obra_id != self.obra_id:
            raise ValidationError({'unidad': 'Debe pertenecer a la obra de la solicitud.'})