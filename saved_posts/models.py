from django.db import models
from django.contrib.auth.models import User
from posts.models import Post

class SavedPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_posts', verbose_name='Usuario')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saved_by', verbose_name='Publicación')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de guardado')

    class Meta:
        unique_together = ('user', 'post')
        verbose_name = 'Publicación guardada'
        verbose_name_plural = 'Publicaciones guardadas'

    def __str__(self):
        return f"{self.user.username} guardó {self.post.id}"