from django.db import models


class PersonajeComparado(models.Model):
    """Personaje de un «X vs Z». Sin personaje aún si está propuesto (solicitud pendiente)."""

    post = models.ForeignKey(
        'posts.Post', on_delete=models.CASCADE, related_name='comparaciones', verbose_name='Publicación',
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