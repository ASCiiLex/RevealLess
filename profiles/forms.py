from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from .models import Profile


class ProfileForm(forms.ModelForm):
    username = forms.CharField(
        validators=[UnicodeUsernameValidator()],
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Usuario',
            'required': True
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Email',
            'required': True
        })
    )

    image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = Profile
        fields = ['bio', 'interests', 'image']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Cuéntanos algo sobre ti...'
            }),
            'interests': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: deporte, programación, música...'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        self.fields['username'].initial = user.username
        self.fields['email'].initial = user.email

        self.fields['image'].widget.clear_checkbox_label = "Eliminar"
        self.fields['image'].widget.initial_text = "Avatar actual"
        self.fields['image'].widget.input_text = "Cambiar"

    def clean(self):
        cleaned = super().clean()

        username = cleaned.get('username')
        email = cleaned.get('email')

        if username and User.objects.filter(username=username).exclude(pk=self.instance.user.pk).exists():
            raise ValidationError("Este nombre de usuario ya está en uso.")

        if email and User.objects.filter(email=email).exclude(pk=self.instance.user.pk).exists():
            raise ValidationError("Este email ya está en uso.")

        return cleaned

    def save(self, user, commit=True):
        profile = super().save(commit=False)

        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.save()

        if commit:
            profile.save()

        return profile