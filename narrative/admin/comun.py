from django import forms
from django.utils.html import format_html

from core.imagenes.remotas import descargar_imagen

# Cambios que alteran orden_inicio/orden_fin de la obra.
CAMPOS_QUE_REORDENAN = {'orden_local', 'padre', 'orden_manual'}

# Lo que usa UnidadNarrativa.__str__: evita una consulta por fila en listados y autocompletes.
RELACIONES_UNIDAD = ('obra', 'padre')


def relaciones_de(campo):
    return tuple(f'{campo}__{rel}' for rel in RELACIONES_UNIDAD)


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


def limitar_unidades_a_obra(campo, obra_id):
    """Selector de unidad restringido a una obra: el queryset valida en servidor y la URL
    del autocomplete lleva ?obra= (lo aplica UnidadNarrativaAdmin.get_search_results)."""
    campo.queryset = campo.queryset.filter(obra_id=obra_id).select_related(*RELACIONES_UNIDAD)
    widget = getattr(campo.widget, 'widget', campo.widget)
    if hasattr(widget, 'get_url'):
        url = widget.get_url()
        widget.get_url = lambda: f'{url}?obra={obra_id}'