from django.contrib.auth.models import User
from django.db import models

from .catalogo import Obra, UnidadNarrativa


class TemaTransversal(models.Model):
    """Hilo temático de una obra sin anclarse a una unidad concreta (ej.
    'Frutas del diablo'), o minihistoria publicada dentro de capítulos
    existentes. Etiqueta de agrupación y suscripción: no participa en
    frontera_orden. Vive en narrative porque es propiedad de la obra."""

    TIPO_TEMATICO = 'tematico'
    TIPO_MINIHISTORIA = 'minihistoria'
    TIPO_CHOICES = [
        (TIPO_TEMATICO, 'Temático'),
        (TIPO_MINIHISTORIA, 'Minihistoria'),
    ]

    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='temas_transversales')
    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_TEMATICO)
    # Solo minihistorias: unidades donde aparece. No implica pertenencia narrativa.
    unidades = models.ManyToManyField(UnidadNarrativa, blank=True, related_name='temas_transversales')

    class Meta:
        unique_together = ('obra', 'nombre')
        ordering = ['nombre']

    def __str__(self):
        return f'{self.obra.titulo} · {self.nombre}'


class SolicitudTema(models.Model):
    """Propuesta de usuario para un TemaTransversal nuevo. Solo se crea el
    tema tras aprobación explícita desde admin."""

    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_APROBADA = 'aprobada'
    ESTADO_RECHAZADA = 'rechazada'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADA, 'Aprobada'),
        (ESTADO_RECHAZADA, 'Rechazada'),
    ]

    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='solicitudes_tema')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes_tema')
    nombre = models.CharField(max_length=150)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE)
    creado_en = models.DateTimeField(auto_now_add=True)
    resuelto_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.usuario.username} propone "{self.nombre}" en {self.obra.titulo} ({self.estado})'