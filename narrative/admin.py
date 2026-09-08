from django.contrib import admin
from .models import Obra, UnidadNarrativa, ProgresoUsuario


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'slug')
    prepopulated_fields = {'slug': ('titulo',)}


@admin.register(UnidadNarrativa)
class UnidadNarrativaAdmin(admin.ModelAdmin):
    list_display = ('obra', 'nombre', 'tipo', 'padre', 'orden_local', 'orden_inicio', 'orden_fin')
    list_filter = ('obra', 'tipo')
    readonly_fields = ('orden_inicio', 'orden_fin')


@admin.register(ProgresoUsuario)
class ProgresoUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'obra', 'unidad_actual', 'orden_absoluto', 'actualizado_en')
    list_filter = ('obra',)
    readonly_fields = ('orden_absoluto',)