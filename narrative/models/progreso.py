from django.contrib.auth.models import User
from django.db import models
from django.db.models import Case, Exists, F, IntegerField, OuterRef, Subquery, Value, When
from django.db.models.functions import Greatest

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


def refrescar_progresos(obra):
    """orden_absoluto se guarda al declarar: tras recalcular el orden de la obra se actualiza
    con el criterio de calcular_orden_absoluto (hoja: su inicio; bloque: justo antes)."""
    tiene_hijos = Exists(UnidadNarrativa.objects.filter(padre=OuterRef('pk')))
    posicion = (
        UnidadNarrativa.objects
        .filter(pk=OuterRef('unidad_actual'))
        .annotate(posicion=Case(
            When(tiene_hijos, then=Greatest(F('orden_inicio') - 1, Value(0), output_field=IntegerField())),
            default=F('orden_inicio'),
            output_field=IntegerField(),
        ))
        .values('posicion')[:1]
    )
    ProgresoUsuario.objects.filter(obra=obra).update(orden_absoluto=Subquery(posicion))