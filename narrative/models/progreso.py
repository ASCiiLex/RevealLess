from django.contrib.auth.models import User
from django.db import models

from .catalogo import Obra, UnidadNarrativa


class ProgresoUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progresos', verbose_name='Usuario')
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='progresos', verbose_name='Obra')
    unidad_actual = models.ForeignKey(UnidadNarrativa, on_delete=models.PROTECT, verbose_name='Unidad actual')
    orden_absoluto = models.PositiveIntegerField(editable=False, default=0, verbose_name='Posición en la obra')
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        unique_together = ('usuario', 'obra')
        verbose_name = 'Progreso de usuario'
        verbose_name_plural = 'Progresos de usuario'

    def __str__(self):
        return f'{self.usuario.username} · {self.obra.titulo} · {self.orden_absoluto}'