from django.db import models
from django.db.models import Count


class HashtagQuerySet(models.QuerySet):
    def visibles_para(self, user):
        """Solo los de publicaciones que el usuario puede ver: el nombre también puede ser un spoiler.
        num_posts cuenta solo esas publicaciones."""
        from .post import Post  # post.py importa este módulo

        return (
            self.filter(posts__post__in=Post.objects.visible_for(user))
            .annotate(num_posts=Count('posts', distinct=True))
        )


class Hashtag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Nombre')

    objects = HashtagQuerySet.as_manager()

    class Meta:
        ordering = ['name']
        verbose_name = 'Hashtag'
        verbose_name_plural = 'Hashtags'

    def __str__(self):
        return f"#{self.name}"


class PostHashtag(models.Model):
    post = models.ForeignKey(
        'posts.Post',
        on_delete=models.CASCADE,
        related_name="post_hashtags",
        verbose_name='Publicación',
    )
    hashtag = models.ForeignKey(
        Hashtag,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name='Hashtag',
    )

    class Meta:
        unique_together = ('post', 'hashtag')
        verbose_name = 'Hashtag de publicación'
        verbose_name_plural = 'Hashtags de publicación'

    def __str__(self):
        return f"{self.post.id} - #{self.hashtag.name}"