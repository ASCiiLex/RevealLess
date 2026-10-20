from django import forms
from django.contrib import admin
from unfold.admin import ModelAdmin

from ..models import SolicitudObra, SolicitudPersonaje, SolicitudTema
from ..services import aprobar_solicitud_tema, rechazar_solicitud_tema
from ..services.personajes import aprobar_solicitud_personaje, rechazar_solicitud_personaje
from ..services.solicitudes_obra import aprobar_solicitud_obra, rechazar_solicitud_obra
from .comun import limitar_unidades_a_obra, relaciones_de


class SolicitudPersonajeForm(forms.ModelForm):
    """La unidad de aparición solo puede elegirse dentro de la obra de la solicitud."""

    class Meta:
        model = SolicitudPersonaje
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and 'unidad' in self.fields:
            limitar_unidades_a_obra(self.fields['unidad'], self.instance.obra_id)


@admin.register(SolicitudPersonaje)
class SolicitudPersonajeAdmin(ModelAdmin):
    form = SolicitudPersonajeForm
    list_display = ('nombre', 'obra', 'unidad', 'personaje', 'usuario', 'estado', 'creado_en')
    # Ajustar la primera aparición o asignar un personaje existente antes de aprobar.
    list_editable = ('unidad', 'personaje')
    list_filter = ('estado', 'obra')
    search_fields = ('nombre', 'obra__titulo', 'usuario__username')
    list_select_related = ('obra', *relaciones_de('unidad'), 'personaje', 'usuario')
    autocomplete_fields = ('obra', 'unidad', 'personaje', 'usuario')
    readonly_fields = ('creado_en', 'resuelto_en')
    actions = ['aprobar_solicitudes', 'rechazar_solicitudes']

    def get_changelist_form(self, request, **kwargs):
        kwargs['form'] = SolicitudPersonajeForm
        return super().get_changelist_form(request, **kwargs)

    @admin.action(description='Aprobar (crea o reutiliza el personaje y lo vincula a sus posts)')
    def aprobar_solicitudes(self, request, queryset):
        procesadas = sum(
            1 for s in queryset.select_related('unidad', 'usuario', 'personaje')
            if aprobar_solicitud_personaje(s) is not None
        )
        self.message_user(request, f'{procesadas} solicitud(es) aprobada(s).')

    @admin.action(description='Rechazar (se retira de los posts que lo esperaban)')
    def rechazar_solicitudes(self, request, queryset):
        procesadas = sum(1 for s in queryset if rechazar_solicitud_personaje(s))
        self.message_user(request, f'{procesadas} solicitud(es) rechazada(s).')


@admin.register(SolicitudTema)
class SolicitudTemaAdmin(ModelAdmin):
    list_display = ('nombre', 'obra', 'usuario', 'estado', 'creado_en', 'resuelto_en')
    list_filter = ('estado', 'obra')
    list_select_related = ('obra', 'usuario')
    readonly_fields = ('resuelto_en',)
    actions = ['aprobar_solicitudes', 'rechazar_solicitudes']

    @admin.action(description='Aprobar solicitudes seleccionadas (crea el tema transversal)')
    def aprobar_solicitudes(self, request, queryset):
        procesadas = sum(1 for s in queryset if aprobar_solicitud_tema(s) is not None)
        self.message_user(request, f'{procesadas} solicitud(es) aprobada(s) y tema(s) creado(s).')

    @admin.action(description='Rechazar solicitudes seleccionadas')
    def rechazar_solicitudes(self, request, queryset):
        procesadas = sum(1 for s in queryset if rechazar_solicitud_tema(s))
        self.message_user(request, f'{procesadas} solicitud(es) rechazada(s).')


@admin.register(SolicitudObra)
class SolicitudObraAdmin(ModelAdmin):
    list_display = ('titulo', 'tipo', 'usuario', 'estado', 'obra', 'enlace', 'creado_en', 'resuelto_en')
    # Si ya existe con otro nombre, se vincula aquí antes de aprobar y no se crea otra.
    list_editable = ('obra',)
    list_filter = ('estado', 'tipo')
    search_fields = ('titulo', 'usuario__username')
    list_select_related = ('obra', 'usuario')
    autocomplete_fields = ('obra', 'usuario')
    readonly_fields = ('creado_en', 'resuelto_en')
    actions = ['aprobar_solicitudes', 'rechazar_solicitudes']

    @admin.action(description='Aprobar (crea la obra con su previo y avisa a quienes la pidieron)')
    def aprobar_solicitudes(self, request, queryset):
        obras = [aprobar_solicitud_obra(s, request.user) for s in queryset.select_related('obra')]
        procesadas = sum(1 for obra in obras if obra is not None)
        self.message_user(request, f'{procesadas} obra(s) añadida(s) al catálogo. Completa su estructura y portada.')

    @admin.action(description='Rechazar (avisa a quienes la pidieron)')
    def rechazar_solicitudes(self, request, queryset):
        procesadas = sum(1 for s in queryset if rechazar_solicitud_obra(s, request.user))
        self.message_user(request, f'{procesadas} sugerencia(s) rechazada(s).')