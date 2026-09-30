from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.contrib.auth.models import User
from narrative.models import ClasificacionNarrativa
from core.validators import validate_image_size
from .managers import PostQuerySet


def post_image_path(instance, filename):
    return f'posts/{instance.author.username}/{filename}'


class Post(ClasificacionNarrativa, models.Model):
    objects = PostQuerySet.as_manager()

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    obra = models.ForeignKey(
        'narrative.Obra',
        on_delete=models.PROTECT,
        related_name='posts'
    )
    text = models.TextField(max_length=500)
    image = models.ImageField(
        upload_to=post_image_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size,
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    is_processed = models.BooleanField(default=False)

    temas_transversales = models.ManyToManyField(
        'narrative.TemaTransversal',
        blank=True,
        related_name='posts',
    )

    personajes = models.ManyToManyField(
        'narrative.Personaje',
        blank=True,
        related_name='posts',
    )

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=~models.Q(frontera_origen=ClasificacionNarrativa.ORIGEN_HEREDADO_POST),
                name='post_frontera_origen_no_heredado',
            ),
            models.CheckConstraint(
                check=models.Q(frontera_spoiler__isnull=False),
                name='post_frontera_spoiler_obligatoria',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(obra_cruzada__isnull=True, frontera_cruzada__isnull=True)
                    | (models.Q(obra_cruzada__isnull=False) & models.Q(frontera_cruzada__isnull=False))
                ),
                name='post_frontera_cruzada_consistency',
            ),
        ]

    def __str__(self):
        return f'Post de {self.author.username} ({self.created_at.date()})'

    def clean(self):
        super().clean()
        if self.referencia_narrativa_id and self.referencia_narrativa.obra_id != self.obra_id:
            raise ValidationError({'referencia_narrativa': 'Debe pertenecer a la obra del post.'})
        if self.frontera_spoiler_id and self.frontera_spoiler.obra_id != self.obra_id:
            raise ValidationError({'frontera_spoiler': 'Debe pertenecer a la obra del post.'})
        if self.obra_cruzada_id:
            if self.obra_cruzada_id == self.obra_id:
                raise ValidationError({'obra_cruzada': 'Debe ser una obra distinta a la del post.'})
            if self.frontera_cruzada_id and self.frontera_cruzada.obra_id != self.obra_cruzada_id:
                raise ValidationError({'frontera_cruzada': 'Debe pertenecer a obra_cruzada.'})

    @property
    def likes_count(self):
        if hasattr(self, "likes_total"):
            return self.likes_total
        from likes.models import PostReaction
        return PostReaction.objects.filter(post=self).count()

    @property
    def comments_count(self):
        if hasattr(self, "comments_total"):
            return self.comments_total
        return self.comments.count()

    @property
    def username_tag(self):
        return f"@{self.author.username}"

    @property
    def image_url(self):
        try:
            if self.image and hasattr(self.image, "url"):
                return self.image.url
        except ValueError:
            pass
        return "/static/img/default_post.jpg"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.is_processed:
            from notifications.utils import extract_hashtags

            tags = extract_hashtags(self.text)

            for tag in tags:
                hashtag, _ = Hashtag.objects.get_or_create(name=tag)
                PostHashtag.objects.get_or_create(
                    post=self,
                    hashtag=hashtag
                )

            self.is_processed = True
            super().save(update_fields=['is_processed'])


class Hashtag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"#{self.name}"


class PostHashtag(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="post_hashtags"
    )
    hashtag = models.ForeignKey(
        Hashtag,
        on_delete=models.CASCADE,
        related_name="posts"
    )

    class Meta:
        unique_together = ('post', 'hashtag')

    def __str__(self):
        return f"{self.post.id} - #{self.hashtag.name}"