from django.contrib import admin
from .models import Obra, UnidadNarrativa, ProgresoUsuario, TemaTransversal, Categoria, SolicitudTema
from .services import aprobar_solicitud_tema, rechazar_solicitud_tema


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'slug')
    list_filter = ('categorias',)
    prepopulated_fields = {'slug': ('titulo',)}
    filter_horizontal = ('categorias',)


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


@admin.register(TemaTransversal)
class TemaTransversalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'obra')
    list_filter = ('obra',)


@admin.register(SolicitudTema)
class SolicitudTemaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'obra', 'usuario', 'estado', 'creado_en', 'resuelto_en')
    list_filter = ('estado', 'obra')
    readonly_fields = ('resuelto_en',)
    actions = ['aprobar_solicitudes', 'rechazar_solicitudes']

    @admin.action(description='Aprobar solicitudes seleccionadas (crea el TemaTransversal)')
    def aprobar_solicitudes(self, request, queryset):
        procesadas = sum(1 for s in queryset if aprobar_solicitud_tema(s) is not None)
        self.message_user(request, f'{procesadas} solicitud(es) aprobada(s) y tema(s) creado(s).')

    @admin.action(description='Rechazar solicitudes seleccionadas')
    def rechazar_solicitudes(self, request, queryset):
        procesadas = sum(1 for s in queryset if rechazar_solicitud_tema(s))
        self.message_user(request, f'{procesadas} solicitud(es) rechazada(s).')