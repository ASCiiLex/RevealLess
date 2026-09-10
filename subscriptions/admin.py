from django.contrib import admin
from .models import Suscripcion, TemaTransversal


@admin.register(TemaTransversal)
class TemaTransversalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'obra')
    list_filter = ('obra',)


@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'obra', 'unidad', 'tema', 'creado_en', 'ultima_visita')
    list_filter = ('obra',)