from django.db import models
from django.contrib.auth.models import User
from posts.models import Post


class PostReaction(models.Model):
    REACTION_CHOICES = [
        ('like', 'Me gusta'),
        ('love', 'Me encanta'),
        ('funny', 'Me divierte'),
        ('wow', 'Me sorprende'),
        ('sad', 'Me entristece'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='post_reactions'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    reaction = models.CharField(
        max_length=10,
        choices=REACTION_CHOICES,
        default='like'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        verbose_name = 'Reacción de post'
        verbose_name_plural = 'Reacciones de posts'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} reaccionó "{self.reaction}" al post {self.post.id}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and self.post.author != self.user:
            from notifications.models import Notification
            from notifications.utils import send_ws_notification

            if not Notification.objects.filter(
                user=self.post.author,
                actor=self.user,
                verb="reacted",
                target_type="post",
                target_id=self.post.id,
                reaction=self.reaction
            ).exists():

                notif = Notification.objects.create(
                    user=self.post.author,
                    actor=self.user,
                    verb="reacted",
                    target_type="post",
                    target_id=self.post.id,
                    reaction=self.reaction
                )

                send_ws_notification(
                    self.post.author,
                    {
                        "id": notif.id,
                        "actor": self.user.username,
                        "verb": "reacted",
                        "target_type": "post",
                        "target_id": self.post.id,
                        "reaction": self.reaction,
                    },
                )