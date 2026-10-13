from django.db import models
from django.db.models import Q

from .catalogo import Obra, UnidadNarrativa


class ExternalId(models.Model):
    """Ancla entre una entidad propia y su ID en una fuente externa.
    Permite reimportar sin duplicar y que Fase B localice lo ya importado."""

    SOURCE_JIKAN = 'jikan'
    SOURCE_MANUAL = 'manual'
    SOURCE_WIKIDATA = 'wikidata'
    SOURCE_CHOICES = [
        (SOURCE_JIKAN, 'Jikan (MyAnimeList)'),
        (SOURCE_MANUAL, 'Curación manual (sin fuente externa)'),
        (SOURCE_WIKIDATA, 'Wikidata'),
    ]

    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, verbose_name='Fuente')
    external_id = models.CharField(max_length=50, verbose_name='ID externo')
    obra = models.ForeignKey(
        Obra, on_delete=models.CASCADE, null=True, blank=True, related_name='external_ids',
        verbose_name='Obra',
    )
    unidad = models.ForeignKey(
        UnidadNarrativa, on_delete=models.CASCADE, null=True, blank=True, related_name='external_ids',
        verbose_name='Unidad narrativa',
    )

    class Meta:
        verbose_name = 'ID externo'
        verbose_name_plural = 'IDs externos'
        constraints = [
            models.CheckConstraint(
                check=(Q(obra__isnull=False) & Q(unidad__isnull=True))
                    | (Q(obra__isnull=True) & Q(unidad__isnull=False)),
                name='externalid_un_solo_destino',
            ),
            models.UniqueConstraint(fields=['source', 'obra'], name='uniq_source_obra', condition=Q(obra__isnull=False)),
            models.UniqueConstraint(fields=['source', 'unidad'], name='uniq_source_unidad', condition=Q(unidad__isnull=False)),
        ]

    def __str__(self):
        return f'{self.source}:{self.external_id}'