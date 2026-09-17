from django.contrib import admin
from .models import (
    Obra, UnidadNarrativa, ProgresoUsuario, TemaTransversal,
    Categoria, SolicitudTema, ExternalId,
)
from .services import aprobar_solicitud_tema, rechazar_solicitud_tema


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'slug', 'autor', 'fecha_publicacion')
    list_filter = ('categorias', 'tipo')
    prepopulated_fields = {'slug': ('titulo',)}
    filter_horizontal = ('categorias',)
    raw_id_fields = ('adapta_a',)  # el propio catálogo de Obras ya no es pequeño


@admin.register(UnidadNarrativa)
class UnidadNarrativaAdmin(admin.ModelAdmin):
    list_display = ('obra', 'nombre', 'tipo', 'padre', 'orden_local', 'orden_inicio', 'orden_fin', 'fecha')
    list_filter = ('obra', 'tipo')
    search_fields = ('nombre',)
    readonly_fields = ('orden_inicio', 'orden_fin')
    # Sin esto, el desplegable de "padre" intenta listar TODAS las unidades
    # de la obra en el HTML del formulario — con 1160+ episodios de One
    # Piece, eso hace el formulario prácticamente inutilizable.
    raw_id_fields = ('padre',)

    # orden_inicio/orden_fin son el valor que consulta frontera_orden — una
    # edición manual de padre/orden_local sin recalcular deja el motor
    # anti-spoiler con datos desactualizados, silenciosamente. Los
    # comandos de importación ya llaman a recalcular_orden() en lote al
    # final; aquí cada edición es unitaria, así que enganchar la llamada
    # directamente en save/delete es seguro (no hay riesgo de recalcular
    # el árbol entero cientos de veces seguidas, como pasaría con un
    # signal post_save durante una importación masiva).
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.obra.recalcular_orden()

    def delete_model(self, request, obj):
        obra = obj.obra
        super().delete_model(request, obj)
        obra.recalcular_orden()

    def delete_queryset(self, request, queryset):
        obras_ids = set(queryset.values_list('obra_id', flat=True))
        super().delete_queryset(request, queryset)
        for obra in Obra.objects.filter(id__in=obras_ids):
            obra.recalcular_orden()


@admin.register(ProgresoUsuario)
class ProgresoUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'obra', 'unidad_actual', 'orden_absoluto', 'actualizado_en')
    list_filter = ('obra',)
    readonly_fields = ('orden_absoluto',)
    raw_id_fields = ('unidad_actual',)  # mismo problema de escala que arriba


@admin.register(TemaTransversal)
class TemaTransversalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'obra', 'tipo')
    list_filter = ('obra', 'tipo')
    search_fields = ('nombre',)
    # raw_id_fields en un M2M da un buscador con lookup en vez de cargar
    # todas las unidades de golpe (que es lo que haría filter_horizontal
    # aquí, con el mismo problema de escala que el padre de arriba).
    raw_id_fields = ('unidades',)


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


@admin.register(ExternalId)
class ExternalIdAdmin(admin.ModelAdmin):
    list_display = ('source', 'external_id', 'obra', 'unidad')
    list_filter = ('source',)
    search_fields = ('external_id', 'obra__titulo', 'unidad__nombre')
    raw_id_fields = ('obra', 'unidad')