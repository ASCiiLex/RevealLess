from django import forms
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from .models import (
    Obra, UnidadNarrativa, ProgresoUsuario, TemaTransversal,
    Categoria, SolicitudTema, ExternalId, Personaje,
)
from .services import aprobar_solicitud_tema, rechazar_solicitud_tema


@admin.register(Categoria)
class CategoriaAdmin(ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


class ObraAdminForm(forms.ModelForm):
    class Meta:
        model = Obra
        fields = '__all__'
        # Solo relabeling de UI -- el campo/columna en BD sigue llamándose
        # adapta_a, esto no toca el modelo ni pide migración.
        labels = {
            'adapta_a': 'Adaptación de',
        }


@admin.register(Obra)
class ObraAdmin(ModelAdmin):
    form = ObraAdminForm
    list_display = ('titulo', 'tipo', 'slug', 'autor', 'fecha_publicacion', 'adapta_a', 'imagen_tag')
    list_filter = ('categorias', 'tipo')
    # Necesario para que el widget autocomplete de otros admins (Post,
    # Comment, ExternalId...) pueda buscar Obras por estos campos.
    search_fields = ('titulo', 'slug')
    prepopulated_fields = {'slug': ('titulo',)}
    filter_horizontal = ('categorias',)
    autocomplete_fields = ('adapta_a',)  # el propio catálogo de Obras ya no es pequeño
    date_hierarchy = 'fecha_publicacion'
    actions = ['recalcular_orden_seleccionadas']

    fieldsets = (
        ('Identidad', {
            'fields': ('titulo', 'slug', 'tipo', 'sinopsis', 'imagen')
        }),
        ('Metadata', {
            'fields': ('autor', 'fecha_publicacion', 'categorias')
        }),
        ('Relaciones narrativas', {
            'fields': ('adapta_a',)
        }),
    )

    def imagen_tag(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" width="40" height="40" style="object-fit:cover;border-radius:6px"/>', obj.imagen.url)
        return "-"
    imagen_tag.short_description = "Portada"

    @admin.action(description='Recalcular orden narrativo de las obras seleccionadas')
    def recalcular_orden_seleccionadas(self, request, queryset):
        for obra in queryset:
            obra.recalcular_orden()
        self.message_user(request, f'{queryset.count()} obra(s) recalculada(s).')


@admin.register(UnidadNarrativa)
class UnidadNarrativaAdmin(ModelAdmin):
    list_display = ('obra', 'nombre', 'tipo', 'padre', 'orden_local', 'orden_inicio', 'orden_fin', 'fecha', 'imagen_tag')
    list_filter = ('obra', 'tipo')
    search_fields = ('nombre',)
    readonly_fields = ('orden_inicio', 'orden_fin')
    # Sin esto, el desplegable de "padre" intenta listar TODAS las unidades
    # de la obra en el HTML del formulario — con 1160+ episodios de One
    # Piece, eso hace el formulario prácticamente inutilizable.
    autocomplete_fields = ('padre',)
    # Reordenar hermanos sin abrir cada ficha. save_model() de abajo ya
    # se invoca por fila cuando Django procesa este guardado en bloque
    # (list_editable no lo salta), así que el recálculo sigue disparándose.
    list_editable = ('orden_local',)

    def imagen_tag(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" width="32" height="32" style="object-fit:cover;border-radius:4px"/>', obj.imagen.url)
        return "-"
    imagen_tag.short_description = "Portada"

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
class ProgresoUsuarioAdmin(ModelAdmin):
    list_display = ('usuario', 'obra', 'unidad_actual', 'orden_absoluto', 'actualizado_en')
    list_filter = ('obra',)
    readonly_fields = ('orden_absoluto',)
    autocomplete_fields = ('unidad_actual',)


@admin.register(TemaTransversal)
class TemaTransversalAdmin(ModelAdmin):
    list_display = ('nombre', 'obra', 'tipo', 'imagen')
    list_filter = ('obra', 'tipo')
    search_fields = ('nombre',)
    autocomplete_fields = ('unidades',)


@admin.register(Personaje)
class PersonajeAdmin(ModelAdmin):
    list_display = ('nombre', 'imagen')
    search_fields = ('nombre',)
    autocomplete_fields = ('unidades',)


@admin.register(SolicitudTema)
class SolicitudTemaAdmin(ModelAdmin):
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
class ExternalIdAdmin(ModelAdmin):
    list_display = ('source', 'external_id', 'obra', 'unidad')
    list_filter = ('source',)
    search_fields = ('external_id', 'obra__titulo', 'unidad__nombre')
    autocomplete_fields = ('obra', 'unidad')