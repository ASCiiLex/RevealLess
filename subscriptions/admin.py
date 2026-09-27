from unfold.admin import ModelAdmin
from django.contrib import admin
from .models import Suscripcion


@admin.register(Suscripcion)
class SuscripcionAdmin(ModelAdmin):
    list_display = ('usuario', 'obra', 'unidad', 'tema', 'creado_en', 'ultima_visita')
    list_filter = ('obra',)