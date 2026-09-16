from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications_sent'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    verb = models.CharField(max_length=255)

    target_type = models.CharField(
        max_length=20,
        choices=[
            ('post', 'Post'),
            ('comment', 'Comment'),
            ('reply', 'Reply'),
            ('follow', 'Follow'),
            ('message', 'Message'),
        ]
    )

    target_id = models.IntegerField(null=True, blank=True)

    reaction = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    seen = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.actor.username} {self.verb}"

    @property
    def avatar(self):
        if hasattr(self.actor, "profile") and self.actor.profile.image:
            return self.actor.profile.image.url
        return "/static/img/default_profile.jpg"

    @property
    def _related_post(self):
        # Cachea la query: post_thumbnail y url ya no piden 2 veces el mismo Post.
        if not hasattr(self, "_post_cache"):
            self._post_cache = None
            if self.target_type in ("post", "comment", "reply") and self.target_id:
                from posts.models import Post
                self._post_cache = Post.objects.only("id", "image").filter(id=self.target_id).first()
        return self._post_cache

    @property
    def post_thumbnail(self):
        post = self._related_post
        if post and post.image:
            return post.image_url
        return "/static/img/default_post.jpg"

    @property
    def url(self):
        # Todas las rutas apuntan a las vistas React (Fase 4) -- las
        # vistas Django clasicas equivalentes siguen existiendo en
        # paralelo, pero las notificaciones deben llevar siempre a la
        # experiencia actual, no a la heredada.
        if self.target_type in ("post", "comment", "reply"):
            if self._related_post:
                return f"/posts/{self.target_id}/react/"
            return f"/notificaciones/post-no-existe/{self.id}/"

        if self.target_type == "follow":
            return f"/perfil/{self.actor.username}/react/"

        if self.target_type == "message":
            return f"/mensajes/chat-react/{self.actor.username}/"

        return "#"