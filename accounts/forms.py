from django import forms
from django.contrib.auth.models import User


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Contraseña',
            'required': True
        })
    )

    password2 = forms.CharField(
        label="Repite la contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Repite la contraseña',
            'required': True
        })
    )

    email = forms.EmailField(
        required=True,
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
        model = User
        fields = ['username', 'email']

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control mb-2',
                'placeholder': 'Usuario',
                'required': True
            }),
        }

    def clean(self):
        cleaned = super().clean()

        username = cleaned.get('username')
        email = cleaned.get('email')
        password = cleaned.get('password')
        password2 = cleaned.get('password2')

        # 🔐 Passwords
        if password and password2 and password != password2:
            self.add_error('password2', "Las contraseñas no coinciden.")

        # 👤 Username único
        if username and User.objects.filter(username=username).exists():
            self.add_error('username', "Este usuario ya existe.")

        # 📧 Email único
        if email and User.objects.filter(email=email).exists():
            self.add_error('email', "Este email ya está registrado.")

        return cleaned