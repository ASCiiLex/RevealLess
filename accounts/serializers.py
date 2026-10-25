from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import FileExtensionValidator
from rest_framework import serializers

from core.validators import validate_image_size

from .validators import USERNAME_MAX, validar_username


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class RegisterSerializer(serializers.Serializer):
    """Validaciones de registro: nombre de usuario con la regla común, contraseñas que coinciden,
    robustez vía validate_password y username/email únicos."""

    username = serializers.CharField(max_length=USERNAME_MAX, validators=[validar_username])
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    # Mismas reglas que Profile.image (extensión y tamaño).
    image = serializers.ImageField(
        required=False,
        allow_null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size,
        ],
    )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Este usuario ya existe.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este email ya está registrado.')
        return value

    def validate(self, data):
        if data.get('password') != data.get('password2'):
            raise serializers.ValidationError({'password2': 'Las contraseñas no coinciden.'})

        try:
            validate_password(
                data.get('password'),
                user=User(username=data.get('username'), email=data.get('email')),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})

        return data

    def create(self, validated_data):
        image = validated_data.pop('image', None)
        validated_data.pop('password2')
        password = validated_data.pop('password')

        user = User.objects.create_user(password=password, **validated_data)

        if image:
            profile = user.profile
            profile.image = image
            profile.save()

        return user


class CambioPasswordSerializer(serializers.Serializer):
    """Exige la contraseña actual; la nueva pasa los mismos validadores que el registro."""

    password_actual = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate_password_actual(self, value):
        if not self.context['user'].check_password(value):
            raise serializers.ValidationError('La contraseña actual no es correcta.')
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Las contraseñas no coinciden.'})

        try:
            validate_password(data['password'], user=self.context['user'])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})

        return data

    def save(self):
        user = self.context['user']
        user.set_password(self.validated_data['password'])
        user.save(update_fields=['password'])
        return user