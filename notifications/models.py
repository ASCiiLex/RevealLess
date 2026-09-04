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
        max_length=10,
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
    def post_thumbnail(self):
        if self.target_type == "post" and self.target_id:
            from posts.models import Post
            post = Post.objects.only("id", "image").filter(id=self.target_id).first()
            if post and post.image:
                return post.image_url
        return "/static/img/default_post.jpg"

    @property
    def url(self):
        if self.target_type in ("post", "comment", "reply"):
            from posts.models import Post
            if Post.objects.filter(id=self.target_id).exists():
                return f"/posts/{self.target_id}/"
            return f"/notificaciones/post-no-existe/{self.id}/"

        if self.target_type == "follow":
            return f"/perfil/{self.actor.username}/"

        if self.target_type == "message":
            return f"/mensajes/{self.actor.username}/"

        return "#"