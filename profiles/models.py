from django.core.validators import FileExtensionValidator
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.validators import validate_image_size

def profile_image_path(instance, filename):
    return f'profiles/{instance.user.username}/{filename}'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    interests = models.CharField(max_length=255, blank=True)
    image = models.ImageField(
        upload_to=profile_image_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size,
        ],
    )

    def __str__(self):
        return f'Perfil de {self.user.username}'

    @property
    def followers_count(self):
        return self.user.followed_by.count()

    @property
    def following_count(self):
        return self.user.following.count()

    @property
    def image_url(self):
        if self.image and hasattr(self.image, "url"):
            try:
                return self.image.url
            except ValueError:
                pass
        return "/static/img/default_profile.jpg"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()