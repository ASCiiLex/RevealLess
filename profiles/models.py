from django.core.validators import FileExtensionValidator
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.imagenes.miniaturas import url_miniatura
from core.validators import validate_image_size

AVATAR_POR_DEFECTO = '/static/img/default_profile.jpg'


def profile_image_path(instance, filename):
    return f'profiles/{instance.user.username}/{filename}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Usuario')
    bio = models.TextField(blank=True, verbose_name='Biografía')
    interests = models.CharField(max_length=255, blank=True, verbose_name='Intereses')
    image = models.ImageField(
        upload_to=profile_image_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size,
        ],
        verbose_name='Foto',
    )

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'

    def __str__(self):
        return f'Perfil de {self.user.username}'

    @property
    def image_url(self):
        """Miniatura: el avatar siempre se pinta pequeño."""
        return url_miniatura(self.image) or AVATAR_POR_DEFECTO


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    Profile.objects.get_or_create(user=instance)