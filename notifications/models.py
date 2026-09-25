from django.db import models
from django.contrib.auth.models import User

# Código guardado en BD -> texto que se muestra al usuario.
VERBOS_TEXTO = {
    'commented': 'comentó tu publicación',
    'replied': 'respondió a tu comentario',
    'mentioned': 'te ha mencionado en un comentario',
}


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
    def verb_display(self):
        """Texto en español del verbo; si no es un código conocido, se devuelve tal cual."""
        if self.verb == 'reacted':
            objetivo = 'comentario' if self.target_type in ('comment', 'reply') else 'publicación'
            return f'reaccionó a tu {objetivo}'
        return VERBOS_TEXTO.get(self.verb, self.verb)

    @property
    def avatar(self):
        if hasattr(self.actor, "profile") and self.actor.profile.image:
            return self.actor.profile.image.url
        return "/static/img/default_profile.jpg"

    @property
    def _related_post(self):
        # Cachea la query: post_thumbnail y url no piden dos veces el mismo Post.
        # target_id es un Post si target_type='post', un Comment si 'comment'/'reply'.
        if not hasattr(self, "_post_cache"):
            self._post_cache = None
            if self.target_id:
                from posts.models import Post
                posts = Post.objects.only("id", "image")
                if self.target_type == "post":
                    self._post_cache = posts.filter(id=self.target_id).first()
                elif self.target_type in ("comment", "reply"):
                    self._post_cache = posts.filter(comments__id=self.target_id).first()
        return self._post_cache

    @property
    def post_thumbnail(self):
        post = self._related_post
        if post and post.image:
            return post.image_url
        return "/static/img/default_post.jpg"

    @property
    def url(self):
        # Todas las rutas apuntan a las vistas React (Fase 4).
        if self.target_type in ("post", "comment", "reply"):
            post = self._related_post
            if post:
                return f"/posts/{post.id}/react/"
            return f"/notificaciones/post-no-existe/{self.id}/"

        if self.target_type == "follow":
            return f"/perfil/{self.actor.username}/"

        if self.target_type == "message":
            return f"/mensajes/{self.actor.username}/"

        return "#"