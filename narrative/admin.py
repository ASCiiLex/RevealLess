from django import forms
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from core.imagenes_remotas import descargar_imagen
from .models import (
    Obra, UnidadNarrativa, ProgresoUsuario, TemaTransversal,
    Categoria, SolicitudTema, ExternalId, Personaje,
)
from .services import aprobar_solicitud_tema, rechazar_solicitud_tema

# Cambios que alteran orden_inicio/orden_fin de la obra.
CAMPOS_QUE_REORDENAN = {'orden_local', 'padre', 'orden_manual'}


class ImagenDesdeUrlForm(forms.ModelForm):
    """Añade 'Imagen desde URL': descarga la imagen y la guarda en el campo 'imagen'."""

    imagen_desde_url = forms.URLField(
        required=False,
        label='Imagen desde URL',
        help_text='Enlace a una imagen jpg, png o webp (máx. 5 MB). Sustituye a la imagen actual.',
    )

    def clean(self):
        cleaned = super().clean()
        url = cleaned.get('imagen_desde_url')
        if url:
            try:
                cleaned['imagen'] = descargar_imagen(url)
            except forms.ValidationError as e:
                self.add_error('imagen_desde_url', e)
        return cleaned


def miniatura(obj, lado=40):
    if obj.imagen:
        return format_html(
            '<img src="{}" width="{}" height="{}" style="object-fit:cover;border-radius:6px"/>',
            obj.imagen.url, lado, lado,
        )
    return '-'


@admin.register(Categoria)
class CategoriaAdmin(ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


class ObraAdminForm(ImagenDesdeUrlForm):
    class Meta:
        model = Obra
        fields = '__all__'
        # Solo relabeling de UI: el campo sigue llamándose adapta_a en BD.
        labels = {
            'adapta_a': 'Adaptación de',
        }


@admin.register(Obra)
class ObraAdmin(ModelAdmin):
    form = ObraAdminForm
    list_display = ('titulo', 'tipo', 'slug', 'autor', 'fecha_publicacion', 'adapta_a', 'imagen_tag')
    list_filter = ('categorias', 'tipo')
    # Necesario para el autocomplete de otros admins (Post, Comment, ExternalId...).
    search_fields = ('titulo', 'slug')
    prepopulated_fields = {'slug': ('titulo',)}
    filter_horizontal = ('categorias',)
    autocomplete_fields = ('adapta_a',)
    date_hierarchy = 'fecha_publicacion'
    actions = ['recalcular_orden_seleccionadas']

    fieldsets = (
        ('Identidad', {
            'fields': ('titulo', 'slug', 'tipo', 'sinopsis', 'imagen', 'imagen_desde_url')
        }),
        ('Metadata', {
            'fields': ('autor', 'fecha_publicacion', 'categorias')
        }),
        ('Relaciones narrativas', {
            'fields': ('adapta_a',)
        }),
    )

    @admin.display(description='Portada')
    def imagen_tag(self, obj):
        return miniatura(obj)

    @admin.action(description='Recalcular orden narrativo de las obras seleccionadas')
    def recalcular_orden_seleccionadas(self, request, queryset):
        for obra in queryset:
            obra.recalcular_orden()
        self.message_user(request, f'{queryset.count()} obra(s) recalculada(s).')


class UnidadNarrativaAdminForm(ImagenDesdeUrlForm):
    class Meta:
        model = UnidadNarrativa
        fields = '__all__'


@admin.register(UnidadNarrativa)
class UnidadNarrativaAdmin(ModelAdmin):
    form = UnidadNarrativaAdminForm
    list_display = ('obra', 'nombre', 'tipo', 'padre', 'orden_local', 'orden_inicio', 'orden_fin', 'fecha', 'imagen_tag')
    list_display_links = ('obra',)
    list_filter = ('obra', 'tipo')
    search_fields = ('nombre',)
    readonly_fields = ('orden_inicio', 'orden_fin')
    # Sin autocomplete, el desplegable de "padre" lista todas las unidades de la obra (1160+ en One Piece).
    autocomplete_fields = ('padre',)
    # Edición en bloque desde el listado: títulos, tipo, fecha y orden.
    list_editable = ('nombre', 'tipo', 'orden_local', 'fecha')

    @admin.display(description='Portada')
    def imagen_tag(self, obj):
        return miniatura(obj, 32)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Recalcular toda la obra solo si cambia el orden: editar títulos en bloque no lo necesita.
        if not change or CAMPOS_QUE_REORDENAN & set(form.changed_data):
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


class TemaTransversalAdminForm(ImagenDesdeUrlForm):
    class Meta:
        model = TemaTransversal
        fields = '__all__'


@admin.register(TemaTransversal)
class TemaTransversalAdmin(ModelAdmin):
    form = TemaTransversalAdminForm
    list_display = ('nombre', 'obra', 'tipo', 'imagen_tag')
    list_filter = ('obra', 'tipo')
    search_fields = ('nombre',)
    autocomplete_fields = ('unidades',)

    @admin.display(description='Imagen')
    def imagen_tag(self, obj):
        return miniatura(obj, 32)


class PersonajeAdminForm(ImagenDesdeUrlForm):
    class Meta:
        model = Personaje
        fields = '__all__'


@admin.register(Personaje)
class PersonajeAdmin(ModelAdmin):
    form = PersonajeAdminForm
    list_display = ('nombre', 'imagen_tag')
    search_fields = ('nombre',)
    autocomplete_fields = ('unidades',)

    @admin.display(description='Imagen')
    def imagen_tag(self, obj):
        return miniatura(obj, 32)


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