from django import forms
from .models import Post
from narrative.models import UnidadNarrativa


class PostForm(forms.ModelForm):
    nuevo_progreso = forms.ModelChoiceField(
        queryset=UnidadNarrativa.objects.none(),
        required=False,
        label='Actualizar mi progreso a (opcional)',
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