from django import forms
from .models import Obra, UnidadNarrativa
from .services import actualizar_progreso


class SeleccionarObraForm(forms.Form):
    obra = forms.ModelChoiceField(queryset=Obra.objects.all(), label='Obra')


class ProgresoForm(forms.Form):
    unidad_actual = forms.ModelChoiceField(
        queryset=UnidadNarrativa.objects.none(),
        label='¿Por dónde vas? (puede ser un episodio concreto o un bloque como una temporada)',
    )
    confirmar_salto = forms.BooleanField(
        required=False,
        label='Confirmo que quiero saltar directamente a este punto (necesario solo para saltos grandes)',
    )

    def __init__(self, *args, obra=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.obra = obra
        if obra:
            self.fields['unidad_actual'].queryset = (
                UnidadNarrativa.objects.filter(obra=obra).order_by('orden_inicio')
            )

    def guardar(self, usuario):
        return actualizar_progreso(
            usuario, self.obra, self.cleaned_data['unidad_actual'],
            confirmado=self.cleaned_data.get('confirmar_salto', False),
        )