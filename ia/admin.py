from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import UsoIA


@admin.register(UsoIA)
class UsoIAAdmin(ModelAdmin):
    """Solo lectura: es un registro de costes, no se edita a mano."""

    list_display = (
        'creado_en', 'funcion', 'modelo', 'usuario', 'obra', 'tokens_entrada',
        'tokens_cache_escritura', 'tokens_cache_lectura', 'tokens_salida',
        'coste_estimado', 'exito', 'duracion_ms',
    )
    list_filter = ('funcion', 'modelo', 'exito')
    list_select_related = ('usuario', 'obra')
    search_fields = ('usuario__username', 'obra__titulo')
    date_hierarchy = 'creado_en'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False