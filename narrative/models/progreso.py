from django.contrib.auth.models import User
from django.db import models

from .catalogo import Obra, UnidadNarrativa


class ProgresoUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progresos')
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='progresos')
    unidad_actual = models.ForeignKey(UnidadNarrativa, on_delete=models.PROTECT)
    orden_absoluto = models.PositiveIntegerField(editable=False, default=0)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('usuario', 'obra')

    def __str__(self):
        return f'{self.usuario.username} · {self.obra.titulo} · {self.orden_absoluto}'