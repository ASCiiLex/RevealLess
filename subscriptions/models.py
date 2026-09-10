from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User


class Suscripcion(models.Model):
    """Una suscripción apunta a exactamente uno de estos tres niveles:
    - obra completa            (unidad=None, tema=None)
    - un nodo del árbol        (unidad=<UnidadNarrativa>, puede ser
                                 intermedio; incluye todo lo que cuelga
                                 por rango orden_inicio/orden_fin)
    - un tema transversal      (tema=<narrative.TemaTransversal>)

    No dispara notificación al crearse un post (a diferencia de Follow):
    es una fuente adicional de feed, siempre filtrada por
    PostQuerySet.visible_for() como cualquier otra. Ver subscriptions/
    services.py para la lógica de resolución de posts."""

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suscripciones')
    obra = models.ForeignKey(
        'narrative.Obra', on_delete=models.CASCADE, related_name='suscripciones'
    )
    unidad = models.ForeignKey(
        'narrative.UnidadNarrativa', on_delete=models.CASCADE, null=True, blank=True,
        related_name='suscripciones',
    )
    tema = models.ForeignKey(
        'narrative.TemaTransversal', on_delete=models.CASCADE, null=True, blank=True,
        related_name='suscripciones',
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    ultima_visita = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creado_en']
        constraints = [
            models.CheckConstraint(
                check=~(models.Q(unidad__isnull=False) & models.Q(tema__isnull=False)),
                name='suscripcion_no_unidad_y_tema_a_la_vez',
            ),
        ]

    def __str__(self):
        objetivo = self.unidad or self.tema or self.obra
        return f'{self.usuario.username} → {objetivo}'

    def clean(self):
        super().clean()
        if self.unidad_id and self.unidad.obra_id != self.obra_id:
            raise ValidationError({'unidad': 'Debe pertenecer a la obra de la suscripción.'})
        if self.tema_id and self.tema.obra_id != self.obra_id:
            raise ValidationError({'tema': 'Debe pertenecer a la obra de la suscripción.'})

    @property
    def nivel(self):
        if self.unidad_id:
            return 'unidad'
        if self.tema_id:
            return 'tema'
        return 'obra'