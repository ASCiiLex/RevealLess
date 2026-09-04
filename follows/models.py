from django.db import models
from django.contrib.auth.models import User
from notifications.models import Notification
from notifications.utils import send_ws_notification


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.follower.username} sigue a {self.followed.username}'

    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args, **kwargs)

        if created:

            notif = Notification.objects.create(
                actor=self.follower,
                user=self.followed,
                verb="te ha seguido",
                target_type="follow"
            )

            send_ws_notification(
                self.followed,
                {
                    "id": notif.id,
                    "actor": self.follower.username,
                    "verb": "te ha seguido",
                    "target_type": "follow",
                }
            )