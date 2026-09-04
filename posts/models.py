from django.db import models
from django.contrib.auth.models import User


def post_image_path(instance, filename):
    return f'posts/{instance.author.username}/{filename}'


class Post(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    text = models.TextField(max_length=500)
    image = models.ImageField(
        upload_to=post_image_path,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # 🔒 Previene ejecución duplicada de lógica (hashtags, etc.)
    is_processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Post de {self.author.username} ({self.created_at.date()})'

    # ❤️ Likes
    @property
    def likes_count(self):
        if hasattr(self, "likes_total"):
            return self.likes_total
        from likes.models import PostReaction
        return PostReaction.objects.filter(post=self).count()

    # 💬 Comentarios
    @property
    def comments_count(self):
        if hasattr(self, "comments_total"):
            return self.comments_total
        return self.comments.count()

    # 🏷️ Username formateado
    @property
    def username_tag(self):
        return f"@{self.author.username}"

    # 🖼️ Imagen segura (nunca rompe)
    @property
    def image_url(self):
        try:
            if self.image and hasattr(self.image, "url"):
                return self.image.url
        except ValueError:
            pass
        return "/static/img/default_post.jpg"

    # 🔥 SAVE ROBUSTO (ANTI DUPLICADOS)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Ejecutar SOLO UNA VEZ
        if not self.is_processed:
            from notifications.utils import extract_hashtags

            tags = extract_hashtags(self.text)

            for tag in tags:
                hashtag, _ = Hashtag.objects.get_or_create(name=tag)
                PostHashtag.objects.get_or_create(
                    post=self,
                    hashtag=hashtag
                )

            # Marcar como procesado
            self.is_processed = True
            super().save(update_fields=['is_processed'])


# 🏷️ Hashtags
class Hashtag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"#{self.name}"


# 🔗 Relación Post-Hashtag
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