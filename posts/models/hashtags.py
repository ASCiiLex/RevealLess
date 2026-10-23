from django.db import models


class Hashtag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Nombre')

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