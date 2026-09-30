from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User


class Suscripcion(models.Model):
    """Una suscripción apunta a exactamente uno de estos niveles:
    - obra completa            (obra, unidad=None, tema=None, personaje=None)
    - un nodo del árbol        (obra + unidad=<UnidadNarrativa>, puede ser
                                 intermedio; incluye todo lo que cuelga
                                 por rango orden_inicio/orden_fin)
    - un tema transversal      (obra + tema=<narrative.TemaTransversal>)
    - un personaje cross-obra  (personaje=<narrative.Personaje>, obra=None
                                 — cruza obras por diseño, no tiene una
                                 obra única a la que anclarse)

    No dispara notificación al crearse un post (a diferencia de Follow):
    es una fuente adicional de feed, siempre filtrada por
    PostQuerySet.visible_for() como cualquier otra. Ver subscriptions/
    services.py para la lógica de resolución de posts.

    activa=False significa 'silenciada': el alcance de esta suscripción
    queda excluido activamente del feed (no solo deja de aportar, sino
    que bloquea el contenido aunque llegue por otra vía como un usuario
    seguido). Prevalece el silencio sobre cualquier otra fuente."""

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suscripciones')
    obra = models.ForeignKey(
        'narrative.Obra', on_delete=models.CASCADE, null=True, blank=True,
        related_name='suscripciones',
    )
    unidad = models.ForeignKey(
        'narrative.UnidadNarrativa', on_delete=models.CASCADE, null=True, blank=True,
        related_name='suscripciones',
    )
    tema = models.ForeignKey(
        'narrative.TemaTransversal', on_delete=models.CASCADE, null=True, blank=True,
        related_name='suscripciones',
    )
    personaje = models.ForeignKey(
        'narrative.Personaje', on_delete=models.CASCADE, null=True, blank=True,
        related_name='suscripciones',
    )
    activa = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    ultima_visita = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creado_en']
        constraints = [
            models.CheckConstraint(
                check=(
                    (models.Q(unidad__isnull=True) | models.Q(tema__isnull=True))
                    & (models.Q(unidad__isnull=True) | models.Q(personaje__isnull=True))
                    & (models.Q(tema__isnull=True) | models.Q(personaje__isnull=True))
                ),
                name='suscripcion_como_mucho_un_nivel_de_alcance',
            ),
            models.CheckConstraint(
                check=(
                    (models.Q(obra__isnull=False) & models.Q(personaje__isnull=True))
                    | (models.Q(obra__isnull=True) & models.Q(personaje__isnull=False))
                ),
                name='suscripcion_obra_xor_personaje',
            ),
        ]

    def __str__(self):
        objetivo = self.unidad or self.tema or self.personaje or self.obra
        estado = '' if self.activa else ' (silenciada)'
        return f'{self.usuario.username} → {objetivo}{estado}'

    def clean(self):
        super().clean()
        if self.personaje_id:
            if self.obra_id or self.unidad_id or self.tema_id:
                raise ValidationError(
                    'Una suscripción a un personaje no puede fijar obra, unidad ni tema.'
                )
            return
        if not self.obra_id:
            raise ValidationError({'obra': 'Obligatoria si no es una suscripción a un personaje.'})
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
        if self.personaje_id:
            return 'personaje'
        return 'obra'