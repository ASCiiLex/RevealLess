from django import forms
from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Count, Q
from unfold.admin import ModelAdmin, TabularInline

from ..models import EtapaPersonaje, Personaje, PropuestaAparicion, RelevanciaPersonaje
from ..services.personajes import (
    aplicar_cambio_propuesta, aprobar_propuesta, eliminar_propuesta, fusionar_personajes, rechazar_propuesta,
)
from .comun import ImagenDesdeUrlForm, limitar_unidades_a_obra, miniatura, relaciones_de


class PersonajeAdminForm(ImagenDesdeUrlForm):
    class Meta:
        model = Personaje
        # Las apariciones se gestionan solo con propuestas (inline), para conservar origen y estado.
        exclude = ('unidades',)


class EtapaPersonajeForm(ImagenDesdeUrlForm):
    class Meta:
        model = EtapaPersonaje
        fields = '__all__'


class PropuestaAparicionForm(forms.ModelForm):
    """Con la propuesta ya creada, la unidad solo puede cambiarse dentro de su obra."""

    class Meta:
        model = PropuestaAparicion
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and 'unidad' in self.fields:
            limitar_unidades_a_obra(self.fields['unidad'], self.instance.unidad.obra_id)


class EtapaPersonajeInline(TabularInline):
    """Etapas: alias, nota, nivel e imagen que se aplican al terminar 'visible_tras'."""

    model = EtapaPersonaje
    form = EtapaPersonajeForm
    extra = 0
    fields = ('visible_tras', 'alias', 'nota', 'nivel', 'imagen', 'imagen_desde_url')
    autocomplete_fields = ('visible_tras',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(*relaciones_de('visible_tras'))


class RelevanciaPersonajeInline(TabularInline):
    """Peso del personaje en cada obra: primer criterio del carrusel de la landing."""

    model = RelevanciaPersonaje
    extra = 0
    fields = ('obra', 'nivel')
    autocomplete_fields = ('obra',)


class PropuestaAparicionInline(TabularInline):
    """Apariciones del personaje. Solo las aprobadas se ven en las landings;
    una fila nueva es una aparición manual."""

    model = PropuestaAparicion
    form = PropuestaAparicionForm
    extra = 0
    fields = ('unidad', 'estado', 'origen', 'confianza', 'nota')
    readonly_fields = ('origen', 'confianza')
    autocomplete_fields = ('unidad',)
    ordering = ('unidad__obra__titulo', 'unidad__orden_inicio')
    show_change_link = True
    verbose_name = 'Aparición'
    verbose_name_plural = 'Apariciones (propuestas y manuales)'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(*relaciones_de('unidad'))


class PendientesFilter(admin.SimpleListFilter):
    title = 'propuestas pendientes'
    parameter_name = 'pendientes'

    def lookups(self, request, model_admin):
        return (('si', 'Con pendientes'), ('no', 'Sin pendientes'))

    def queryset(self, request, queryset):
        # Usa la anotación 'pendientes' de PersonajeAdmin.get_queryset.
        if self.value() == 'si':
            return queryset.filter(pendientes__gt=0)
        if self.value() == 'no':
            return queryset.filter(pendientes=0)
        return queryset


@admin.register(Personaje)
class PersonajeAdmin(ModelAdmin):
    form = PersonajeAdminForm
    list_display = (
        'nombre', 'identidad_de', 'wikidata_id', 'total_apariciones', 'total_etapas', 'total_pendientes',
        'imagen_tag',
    )
    list_filter = (
        ('unidades__obra', admin.RelatedOnlyFieldListFilter),
        'relevancias__nivel',
        PendientesFilter,
        ('imagen', admin.EmptyFieldListFilter),
        ('wikidata_id', admin.EmptyFieldListFilter),
        ('identidad_de', admin.EmptyFieldListFilter),
    )
    search_fields = ('nombre', 'wikidata_id', 'etapas__alias')
    autocomplete_fields = ('identidad_de', 'identidad_revelada_tras')
    inlines = [RelevanciaPersonajeInline, EtapaPersonajeInline, PropuestaAparicionInline]
    actions = ['fusionar_seleccionados']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('identidad_de').annotate(
            apariciones=Count('unidades', distinct=True),
            num_etapas=Count('etapas', distinct=True),
            pendientes=Count(
                'propuestas',
                filter=Q(propuestas__estado=PropuestaAparicion.ESTADO_PENDIENTE),
                distinct=True,
            ),
        )

    def save_formset(self, request, form, formset, change):
        if formset.model is not PropuestaAparicion:
            return super().save_formset(request, form, formset, change)

        # Estado y unidad en BD antes de guardar: decide qué apariciones añadir o retirar.
        ids = [f.instance.pk for f in formset.initial_forms if f.instance.pk]
        previos = {
            pk: (estado, unidad_id)
            for pk, estado, unidad_id in PropuestaAparicion.objects.filter(pk__in=ids)
            .values_list('pk', 'estado', 'unidad_id')
        }
        borradas = [f.instance.pk for f in formset.deleted_forms if f.instance.pk]

        formset.save()

        for pk in borradas:
            estado, unidad_id = previos[pk]
            if estado == PropuestaAparicion.ESTADO_APROBADA:
                form.instance.unidades.remove(unidad_id)
        for propuesta in formset.new_objects:
            aplicar_cambio_propuesta(propuesta)
        for propuesta, _campos in formset.changed_objects:
            aplicar_cambio_propuesta(propuesta, *previos[propuesta.pk])

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

    @admin.action(description='Fusionar seleccionados en uno (se conserva el de Wikidata o con más apariciones)')
    def fusionar_seleccionados(self, request, queryset):
        personajes = list(queryset)
        if len(personajes) < 2:
            self.message_user(request, 'Selecciona al menos dos personajes.', messages.WARNING)
            return
        destino = max(personajes, key=lambda p: (p.wikidata_id is not None, p.apariciones, -p.pk))
        with transaction.atomic():
            for personaje in personajes:
                if personaje.pk != destino.pk:
                    fusionar_personajes(personaje, destino)
        self.message_user(request, f'{len(personajes) - 1} personaje(s) fusionado(s) en «{destino}».')


@admin.register(RelevanciaPersonaje)
class RelevanciaPersonajeAdmin(ModelAdmin):
    """Marcar protagonistas y principales obra a obra; el nivel se edita desde la lista."""

    list_display = ('personaje', 'obra', 'nivel')
    list_editable = ('nivel',)
    list_filter = ('obra', 'nivel')
    search_fields = ('personaje__nombre', 'obra__titulo')
    list_select_related = ('personaje', 'obra')
    autocomplete_fields = ('personaje', 'obra')


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
    form = PropuestaAparicionForm
    list_display = ('personaje', 'obra', 'unidad', 'origen', 'confianza', 'estado', 'nota', 'creado_en')
    # Corregir la unidad desde el listado (solo dentro de su obra); si estaba aprobada, la aparición se mueve.
    list_editable = ('unidad',)
    list_filter = ('estado', 'origen', ConfianzaFilter, 'unidad__obra')
    search_fields = ('personaje__nombre', 'unidad__nombre', 'unidad__obra__titulo')
    list_select_related = ('personaje', *relaciones_de('unidad'))
    autocomplete_fields = ('personaje', 'unidad')
    readonly_fields = ('resuelto_en', 'creado_en')
    actions = ['aprobar_propuestas', 'rechazar_propuestas']

    @admin.display(description='Obra', ordering='unidad__obra__titulo')
    def obra(self, obj):
        return obj.unidad.obra

    def get_changelist_form(self, request, **kwargs):
        kwargs['form'] = PropuestaAparicionForm
        return super().get_changelist_form(request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Leído de BD: el formulario del listado no trae el estado.
        previo = None
        if change:
            previo = PropuestaAparicion.objects.filter(pk=obj.pk).values_list('estado', 'unidad_id').first()
        super().save_model(request, obj, form, change)
        aplicar_cambio_propuesta(obj, *(previo or (None, None)))

    def delete_model(self, request, obj):
        eliminar_propuesta(obj)

    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for propuesta in queryset.select_related('personaje'):
                eliminar_propuesta(propuesta)

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