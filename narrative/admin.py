from django import forms
from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from core.imagenes_remotas import descargar_imagen
from .models import (
    Obra, UnidadNarrativa, ProgresoUsuario, TemaTransversal, Categoria, SolicitudTema,
    ExternalId, Personaje, EtapaPersonaje, PropuestaAparicion,
)
from .services import aprobar_solicitud_tema, rechazar_solicitud_tema
from .services.personajes import aprobar_propuesta, rechazar_propuesta

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
    search_fields = ('nombre', 'obra__titulo')
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


class EtapaPersonajeForm(ImagenDesdeUrlForm):
    class Meta:
        model = EtapaPersonaje
        fields = '__all__'


class EtapaPersonajeInline(TabularInline):
    """Etapas: alias, nota e imagen que se revelan al terminar 'visible_tras'."""

    model = EtapaPersonaje
    form = EtapaPersonajeForm
    extra = 0
    fields = ('visible_tras', 'alias', 'nota', 'imagen', 'imagen_desde_url')
    autocomplete_fields = ('visible_tras',)


class PropuestaAparicionInline(TabularInline):
    """Solo consulta: las propuestas se revisan desde su propio listado."""

    model = PropuestaAparicion
    extra = 0
    fields = ('unidad', 'origen', 'confianza', 'estado', 'nota')
    readonly_fields = fields
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Personaje)
class PersonajeAdmin(ModelAdmin):
    form = PersonajeAdminForm
    list_display = ('nombre', 'wikidata_id', 'total_apariciones', 'total_etapas', 'total_pendientes', 'imagen_tag')
    search_fields = ('nombre', 'wikidata_id', 'etapas__alias')
    autocomplete_fields = ('unidades',)
    inlines = [EtapaPersonajeInline, PropuestaAparicionInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            apariciones=Count('unidades', distinct=True),
            num_etapas=Count('etapas', distinct=True),
            pendientes=Count(
                'propuestas',
                filter=Q(propuestas__estado=PropuestaAparicion.ESTADO_PENDIENTE),
                distinct=True,
            ),
        )

    @admin.display(description='Apariciones', ordering='apariciones')
    def total_apariciones(self, obj):
        return obj.apariciones

    @admin.display(description='Etapas', ordering='num_etapas')
    def total_etapas(self, obj):
        return obj.num_etapas

    @admin.display(description='Pendientes', ordering='pendientes')
    def total_pendientes(self, obj):
        return obj.pendientes

    @admin.display(description='Imagen')
    def imagen_tag(self, obj):
        return miniatura(obj, 32)


class ConfianzaFilter(admin.SimpleListFilter):
    title = 'confianza'
    parameter_name = 'confianza'

    def lookups(self, request, model_admin):
        return (('alta', '≥ 0,8'), ('media', '0,6 – 0,8'), ('baja', '< 0,6'), ('sin', 'Sin dato'))

    def queryset(self, request, queryset):
        valor = self.value()
        if valor == 'alta':
            return queryset.filter(confianza__gte=0.8)
        if valor == 'media':
            return queryset.filter(confianza__gte=0.6, confianza__lt=0.8)
        if valor == 'baja':
            return queryset.filter(confianza__lt=0.6)
        if valor == 'sin':
            return queryset.filter(confianza__isnull=True)
        return queryset


@admin.register(PropuestaAparicion)
class PropuestaAparicionAdmin(ModelAdmin):
    list_display = ('personaje', 'obra', 'unidad', 'origen', 'confianza', 'estado', 'nota', 'creado_en')
    list_filter = ('estado', 'origen', ConfianzaFilter, 'unidad__obra')
    search_fields = ('personaje__nombre', 'unidad__nombre', 'unidad__obra__titulo')
    list_select_related = ('personaje', 'unidad__obra')
    autocomplete_fields = ('personaje', 'unidad')
    readonly_fields = ('estado', 'resuelto_en', 'creado_en')
    actions = ['aprobar_propuestas', 'rechazar_propuestas']

    @admin.display(description='Obra', ordering='unidad__obra__titulo')
    def obra(self, obj):
        return obj.unidad.obra

    @admin.action(description='Aprobar (el personaje pasa a ser visible desde esa unidad)')
    def aprobar_propuestas(self, request, queryset):
        propuestas = list(queryset.select_related('personaje', 'unidad'))
        for propuesta in propuestas:
            aprobar_propuesta(propuesta)
        self.message_user(request, f'{len(propuestas)} propuesta(s) aprobada(s).')

    @admin.action(description='Rechazar (y retirar si estaba aprobada)')
    def rechazar_propuestas(self, request, queryset):
        propuestas = list(queryset.select_related('personaje', 'unidad'))
        for propuesta in propuestas:
            rechazar_propuesta(propuesta)
        self.message_user(request, f'{len(propuestas)} propuesta(s) rechazada(s).')


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