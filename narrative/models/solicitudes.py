from django.contrib.auth.models import User
from django.db import models

from .catalogo import Obra


class SolicitudObra(models.Model):
    """Obra que un usuario echa en falta en el catálogo. Al aprobarla se crea (o se vincula una
    existente) con su «Previo al estreno» y se avisa a todos los que la pidieron.
    Mismo patrón que SolicitudTema."""

    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_APROBADA = 'aprobada'
    ESTADO_RECHAZADA = 'rechazada'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADA, 'Aprobada'),
        (ESTADO_RECHAZADA, 'Rechazada'),
    ]

    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='solicitudes_obra', verbose_name='Usuario',
    )
    titulo = models.CharField(max_length=200, verbose_name='Título')
    tipo = models.CharField(max_length=20, choices=Obra.TIPO_CHOICES, default=Obra.TIPO_SERIE, verbose_name='Tipo')
    enlace = models.URLField(blank=True, verbose_name='Enlace de referencia')
    comentario = models.CharField(max_length=300, blank=True, verbose_name='Comentario')
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE, verbose_name='Estado',
    )
    obra = models.ForeignKey(
        Obra, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes',
        verbose_name='Obra',
        help_text='Vacío: se crea al aprobar. Elige una si ya existe con otro nombre.',
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    resuelto_en = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de resolución')

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Solicitud de obra'
        verbose_name_plural = 'Solicitudes de obra'

    def __str__(self):
        return f'{self.usuario.username} sugiere «{self.titulo}» ({self.estado})'