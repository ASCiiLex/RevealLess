from django import forms
from django.forms.models import construct_instance
from .models import Post
from narrative.models import UnidadNarrativa


class PostForm(forms.ModelForm):
    nuevo_progreso = forms.ModelChoiceField(
        queryset=UnidadNarrativa.objects.none(),
        required=False,
        label='Actualizar mi progreso a (opcional)',
    )
    confirmar_salto_progreso = forms.BooleanField(
        required=False,
        label='Confirmo el salto de progreso si es grande',
    )

    class Meta:
        model = Post
        fields = ['text', 'image', 'referencia_narrativa', 'frontera_spoiler', 'nivel_spoiler']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '¿Qué estás pensando?',
                'rows': 3
            }),
        }
        labels = {
            'frontera_spoiler': 'Frontera de spoiler (opcional; si no se indica, se usa tu progreso actual)',
        }

    def __init__(self, *args, obra=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.obra = obra
        if obra:
            unidades = UnidadNarrativa.objects.filter(obra=obra).order_by('orden_inicio')
            self.fields['referencia_narrativa'].queryset = unidades
            self.fields['frontera_spoiler'].queryset = unidades
            self.fields['nuevo_progreso'].queryset = unidades

    def _post_clean(self):
        # Ver nota en la versión anterior: 'obra' no es campo del form y
        # 'frontera_spoiler' puede quedar vacío a propósito (lo completa la
        # IA/fallback en la vista), así que la validación de instancia
        # completa se hace explícitamente ahí, no aquí.
        opts = self._meta
        construct_instance(self, self.instance, opts.fields, opts.exclude)