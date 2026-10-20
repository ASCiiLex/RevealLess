from django.contrib.auth.models import User
from django.db import models


class UsoIA(models.Model):
    """Una llamada a la API de Anthropic: base del control de costes por función, usuario y obra.
    Solo métricas: ni el prompt ni la respuesta se guardan (podrían contener spoilers)."""

    FUNCION_CLASIFICACION = 'clasificacion'
    FUNCION_SUGERENCIA = 'sugerencia'
    FUNCION_PERSONAJES = 'personajes'
    FUNCION_APARICIONES = 'apariciones'
    FUNCION_TRADUCCION = 'traduccion'
    FUNCION_EVALUACION = 'evaluacion'
    FUNCION_CHOICES = [
        (FUNCION_CLASIFICACION, 'Frontera al publicar'),
        (FUNCION_SUGERENCIA, 'Sugerencia de frontera'),
        (FUNCION_PERSONAJES, 'Propuesta de personajes'),
        (FUNCION_APARICIONES, 'Primeras apariciones'),
        (FUNCION_TRADUCCION, 'Traducción del catálogo'),
        (FUNCION_EVALUACION, 'Evaluación de fronteras'),
    ]

    creado_en = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Fecha')
    funcion = models.CharField(max_length=30, choices=FUNCION_CHOICES, verbose_name='Función')
    modelo = models.CharField(max_length=100, verbose_name='Modelo')
    # Opcionales: los comandos de catálogo no tienen usuario y la traducción agrupa varias obras.
    usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='usos_ia', verbose_name='Usuario',
    )
    obra = models.ForeignKey(
        'narrative.Obra', on_delete=models.SET_NULL, null=True, blank=True, related_name='usos_ia',
        verbose_name='Obra',
    )
    # Entrada sin caché; la cacheada va aparte porque se factura a otro precio.
    tokens_entrada = models.PositiveIntegerField(default=0, verbose_name='Tokens de entrada')
    tokens_cache_escritura = models.PositiveIntegerField(default=0, verbose_name='Tokens escritos en caché')
    tokens_cache_lectura = models.PositiveIntegerField(default=0, verbose_name='Tokens leídos de caché')
    tokens_salida = models.PositiveIntegerField(default=0, verbose_name='Tokens de salida')
    # USD según los precios en el momento de la llamada; vacío si el modelo no tiene precio configurado.
    coste_estimado = models.DecimalField(
        max_digits=12, decimal_places=6, null=True, blank=True, verbose_name='Coste estimado (USD)',
    )
    exito = models.BooleanField(default=True, verbose_name='Éxito')
    duracion_ms = models.PositiveIntegerField(null=True, blank=True, verbose_name='Duración (ms)')

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Uso de IA'
        verbose_name_plural = 'Usos de IA'

    def __str__(self):
        return f'{self.get_funcion_display()} · {self.modelo} · {self.creado_en:%Y-%m-%d %H:%M}'