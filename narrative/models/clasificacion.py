from django.db import models
from django.db.models import OuterRef, Subquery

from .catalogo import Obra, UnidadNarrativa, expresion_orden_frontera

# FK a UnidadNarrativa → campo donde se cachea su posición.
CAMPOS_FRONTERA = {
    'frontera_spoiler': 'frontera_orden',
    'frontera_cruzada': 'frontera_cruzada_orden',
}


class ClasificacionNarrativa(models.Model):
    """Mixin abstracto de Post y Comment. frontera_orden es el valor que
    consulta el motor de visibilidad.

    obra_cruzada / frontera_cruzada: contenido de una obra que revela
    información de otra continuidad. Si están informados, se exige además
    progreso en obra_cruzada. Siempre declarativo, nunca inferido.

    emocion_autor: emoción declarada por el autor. No afecta a visibilidad."""

    ORIGEN_EXPLICITO = 'explicito'
    ORIGEN_IA = 'ia'
    ORIGEN_FALLBACK = 'fallback'
    ORIGEN_HEREDADO_POST = 'heredado_post'
    ORIGEN_ADMIN = 'admin'
    ORIGEN_CHOICES = [
        (ORIGEN_EXPLICITO, 'Explícito'),
        (ORIGEN_IA, 'IA'),
        (ORIGEN_FALLBACK, 'Progreso del autor'),
        (ORIGEN_HEREDADO_POST, 'Heredado del post'),
        (ORIGEN_ADMIN, 'Corrección administrativa'),
    ]

    NIVEL_MENOR = 'menor'
    NIVEL_IMPORTANTE = 'importante'
    NIVEL_TRAMA_CENTRAL = 'trama_central'
    NIVEL_CHOICES = [
        (NIVEL_MENOR, 'Menor'),
        (NIVEL_IMPORTANTE, 'Importante'),
        (NIVEL_TRAMA_CENTRAL, 'Trama central'),
    ]

    EMOCION_ME_GUSTA = 'me_gusta'
    EMOCION_ME_ENCANTA = 'me_encanta'
    EMOCION_ME_DIVIERTE = 'me_divierte'
    EMOCION_ME_SORPRENDE = 'me_sorprende'
    EMOCION_ME_ENFADA = 'me_enfada'
    EMOCION_ME_DA_ASCO = 'me_da_asco'
    EMOCION_ME_ENTRISTECE = 'me_entristece'
    EMOCION_ME_ENTUSIASMA = 'me_entusiasma'
    EMOCION_ME_EMOCIONA = 'me_emociona'
    EMOCION_ME_DA_CURIOSIDAD = 'me_da_curiosidad'
    EMOCION_ME_DA_MIEDO = 'me_da_miedo'
    EMOCION_CHOICES = [
        (EMOCION_ME_GUSTA, 'Me gusta'),
        (EMOCION_ME_ENCANTA, 'Me encanta'),
        (EMOCION_ME_DIVIERTE, 'Me divierte'),
        (EMOCION_ME_SORPRENDE, 'Me sorprende'),
        (EMOCION_ME_ENFADA, 'Me enfada'),
        (EMOCION_ME_DA_ASCO, 'Me da asco'),
        (EMOCION_ME_ENTRISTECE, 'Me entristece'),
        (EMOCION_ME_ENTUSIASMA, 'Me entusiasma'),
        (EMOCION_ME_EMOCIONA, 'Me emociona'),
        (EMOCION_ME_DA_CURIOSIDAD, 'Me da curiosidad'),
        (EMOCION_ME_DA_MIEDO, 'Me da miedo'),
    ]

    referencia_narrativa = models.ForeignKey(
        UnidadNarrativa, on_delete=models.PROTECT,
        related_name='%(class)s_referenciados', verbose_name='Referencia narrativa',
    )
    frontera_spoiler = models.ForeignKey(
        UnidadNarrativa, on_delete=models.PROTECT, null=True, blank=True,
        related_name='%(class)s_frontera', verbose_name='Frontera de spoiler',
    )
    frontera_orden = models.PositiveIntegerField(
        null=True, blank=True, editable=False, verbose_name='Posición de la frontera',
    )
    frontera_origen = models.CharField(max_length=20, choices=ORIGEN_CHOICES, verbose_name='Origen de la frontera')
    nivel_spoiler = models.CharField(
        max_length=20, choices=NIVEL_CHOICES, default=NIVEL_MENOR, verbose_name='Nivel de spoiler',
    )
    ia_confianza = models.FloatField(null=True, blank=True, verbose_name='Confianza de la IA')
    clasificado_en = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de clasificación')

    emocion_autor = models.CharField(
        max_length=20, choices=EMOCION_CHOICES, null=True, blank=True, verbose_name='Emoción del autor',
    )

    obra_cruzada = models.ForeignKey(
        Obra, on_delete=models.PROTECT, null=True, blank=True,
        related_name='%(class)s_cruzados',
        verbose_name='Obra cruzada',
        help_text='Obra distinta (ej. manga si esto es del anime) cuya frontera también debe cumplirse.',
    )
    frontera_cruzada = models.ForeignKey(
        UnidadNarrativa, on_delete=models.PROTECT, null=True, blank=True,
        related_name='%(class)s_frontera_cruzada',
        verbose_name='Frontera cruzada',
        help_text='Punto de obra_cruzada hasta el que hay que haber llegado.',
    )
    frontera_cruzada_orden = models.PositiveIntegerField(
        null=True, blank=True, editable=False, verbose_name='Posición de la frontera cruzada',
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.frontera_origen == self.ORIGEN_HEREDADO_POST:
            self.frontera_orden = None
        elif self.frontera_spoiler_id:
            self.frontera_orden = self.frontera_spoiler.orden_frontera

        self.frontera_cruzada_orden = (
            self.frontera_cruzada.orden_frontera if self.frontera_cruzada_id else None
        )

        super().save(*args, **kwargs)


def refrescar_fronteras(obra):
    """Las posiciones de frontera se cachean al guardar: tras recalcular el orden de la obra
    se actualizan en bloque, o el motor compararía contra posiciones antiguas.
    Recorre las relaciones inversas para no importar posts ni comments desde narrative."""
    for relacion in UnidadNarrativa._meta.related_objects:
        campo_fk = relacion.field.name
        campo_cache = CAMPOS_FRONTERA.get(campo_fk)
        if campo_cache is None or not issubclass(relacion.related_model, ClasificacionNarrativa):
            continue
        orden = (
            UnidadNarrativa.objects
            .filter(pk=OuterRef(campo_fk))
            .annotate(posicion=expresion_orden_frontera())
            .values('posicion')[:1]
        )
        relacion.related_model.objects.filter(**{f'{campo_fk}__obra': obra}).update(
            **{campo_cache: Subquery(orden)}
        )