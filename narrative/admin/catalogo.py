from django import forms
from django.contrib import admin
from unfold.admin import ModelAdmin

from ..models import Categoria, ExternalId, Obra, ProgresoUsuario, TemaTransversal, UnidadNarrativa
from ..services import asegurar_unidad_previa
from ..services.previos import crear_previo
from .comun import (
    CAMPOS_QUE_REORDENAN, RELACIONES_UNIDAD, ImagenDesdeUrlForm, miniatura, relaciones_de,
)


@admin.register(Categoria)
class CategoriaAdmin(ModelAdmin):
    list_display = ('nombre', 'es_universo')
    list_editable = ('es_universo',)
    list_filter = ('es_universo',)
    search_fields = ('nombre',)


class ObraAdminForm(ImagenDesdeUrlForm):
    class Meta:
        model = Obra
        fields = '__all__'


class ObraListadoForm(forms.ModelForm):
    """Portada en el listado: input nativo (ruta + limpiar); la miniatura ya va en su columna."""

    class Meta:
        model = Obra
        fields = ('imagen',)
        widgets = {'imagen': forms.ClearableFileInput}


@admin.register(Obra)
class ObraAdmin(ModelAdmin):
    form = ObraAdminForm
    list_display = ('titulo', 'tipo', 'slug', 'autor', 'fecha_publicacion', 'adapta_a', 'imagen_tag', 'imagen')
    # Portada subible desde el listado; la URL sigue en la ficha (no es campo del modelo).
    list_editable = ('imagen',)
    list_filter = ('categorias', 'tipo')
    # Necesario para el autocomplete de otros admins (Post, Comment, ExternalId...).
    search_fields = ('titulo', 'slug')
    prepopulated_fields = {'slug': ('titulo',)}
    filter_horizontal = ('categorias',)
    autocomplete_fields = ('adapta_a',)
    date_hierarchy = 'fecha_publicacion'
    actions = ['recalcular_orden_seleccionadas', 'crear_previo_obras_sin_estructura']

    fieldsets = (
        ('Identidad', {
            'fields': ('titulo', 'slug', 'tipo', 'sinopsis', 'imagen', 'imagen_desde_url')
        }),
        ('Metadatos', {
            'fields': ('autor', 'fecha_publicacion', 'categorias')
        }),
        ('Relaciones narrativas', {
            'fields': ('adapta_a',)
        }),
    )

    def get_changelist_form(self, request, **kwargs):
        kwargs['form'] = ObraListadoForm
        return super().get_changelist_form(request, **kwargs)

    @admin.display(description='Portada')
    def imagen_tag(self, obj):
        return miniatura(obj)

    @admin.action(description='Recalcular orden narrativo de las obras seleccionadas')
    def recalcular_orden_seleccionadas(self, request, queryset):
        for obra in queryset:
            obra.recalcular_orden()
        self.message_user(request, f'{queryset.count()} obra(s) recalculada(s).')

    @admin.action(description='Crear «Previo al estreno» en las obras sin estructura')
    def crear_previo_obras_sin_estructura(self, request, queryset):
        creados = sum(1 for obra in queryset if asegurar_unidad_previa(obra))
        self.message_user(request, f'{creados} previo(s) creado(s); las obras con unidades no cambian.')


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
    # padre__nombre: «shippūden 138» encuentra el episodio dentro de esa temporada.
    search_fields = ('nombre', 'obra__titulo', 'padre__nombre')
    readonly_fields = ('orden_inicio', 'orden_fin')
    # Sin autocomplete, el desplegable de "padre" lista todas las unidades de la obra (1160+ en One Piece).
    autocomplete_fields = ('padre',)
    # Edición en bloque desde el listado: títulos, tipo, fecha y orden.
    list_editable = ('nombre', 'tipo', 'orden_local', 'fecha')
    actions = ['crear_previo_seleccionadas']

    def get_queryset(self, request):
        # También lo usa el autocomplete; padre__* cubre la columna «padre» del listado.
        return super().get_queryset(request).select_related('obra', 'padre__obra', 'padre__padre')

    def get_search_results(self, request, queryset, search_term):
        # Autocompletes limitados a una obra (limitar_unidades_a_obra añade ?obra=).
        obra_id = request.GET.get('obra', '')
        if obra_id.isdigit():
            queryset = queryset.filter(obra_id=obra_id)
        return super().get_search_results(request, queryset, search_term)

    @admin.display(description='Portada')
    def imagen_tag(self, obj):
        return miniatura(obj, 32)

    @admin.action(description='Crear «Previo» justo antes de las unidades seleccionadas')
    def crear_previo_seleccionadas(self, request, queryset):
        previos = [crear_previo(unidad) for unidad in queryset if not unidad.es_previa]
        self.message_user(
            request,
            f'{len(previos)} previo(s) listo(s). Fija su fecha de estreno si la entrega aún no tiene episodios con fecha.',
        )

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
    list_select_related = ('usuario', 'obra', *relaciones_de('unidad_actual'))
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


@admin.register(ExternalId)
class ExternalIdAdmin(ModelAdmin):
    list_display = ('source', 'external_id', 'obra', 'unidad')
    list_filter = ('source',)
    search_fields = ('external_id', 'obra__titulo', 'unidad__nombre')
    list_select_related = ('obra', *relaciones_de('unidad'))
    autocomplete_fields = ('obra', 'unidad')