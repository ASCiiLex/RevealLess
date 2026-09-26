from django.db import models

from .catalogo import Obra, UnidadNarrativa


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
        (ORIGEN_FALLBACK, 'Fallback'),
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
        related_name='%(class)s_referenciados',
    )
    frontera_spoiler = models.ForeignKey(
        UnidadNarrativa, on_delete=models.PROTECT, null=True, blank=True,
        related_name='%(class)s_frontera',
    )
    frontera_orden = models.PositiveIntegerField(null=True, blank=True, editable=False)
    frontera_origen = models.CharField(max_length=20, choices=ORIGEN_CHOICES)
    nivel_spoiler = models.CharField(max_length=20, choices=NIVEL_CHOICES, default=NIVEL_MENOR)
    ia_confianza = models.FloatField(null=True, blank=True)
    clasificado_en = models.DateTimeField(null=True, blank=True)

    emocion_autor = models.CharField(
        max_length=20, choices=EMOCION_CHOICES, null=True, blank=True,
    )

    obra_cruzada = models.ForeignKey(
        Obra, on_delete=models.PROTECT, null=True, blank=True,
        related_name='%(class)s_cruzados',
        help_text='Obra distinta (ej. manga si esto es del anime) cuya frontera también debe cumplirse.',
    )
    frontera_cruzada = models.ForeignKey(
        UnidadNarrativa, on_delete=models.PROTECT, null=True, blank=True,
        related_name='%(class)s_frontera_cruzada',
        help_text='Punto de obra_cruzada hasta el que hay que haber llegado.',
    )
    frontera_cruzada_orden = models.PositiveIntegerField(null=True, blank=True, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.frontera_origen == self.ORIGEN_HEREDADO_POST:
            self.frontera_orden = None
        elif self.frontera_spoiler_id:
            self.frontera_orden = self.frontera_spoiler.orden_fin

        self.frontera_cruzada_orden = (
            self.frontera_cruzada.orden_fin if self.frontera_cruzada_id else None
        )

        super().save(*args, **kwargs)