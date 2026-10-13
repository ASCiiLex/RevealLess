from django.db import models
from django.contrib.auth.models import User
from notifications.models import Notification
from notifications.utils import send_ws_notification


class Follow(models.Model):
    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following", verbose_name='Seguidor',
    )
    followed = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followed_by", verbose_name='Seguido',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')

    class Meta:
        unique_together = ("follower", "followed")
        ordering = ["-created_at"]
        verbose_name = 'Seguimiento'
        verbose_name_plural = 'Seguimientos'

    def __str__(self):
        return f"{self.follower.username} sigue a {self.followed.username}"

    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args, **kwargs)
        if created:
            notif = Notification.objects.create(
                actor=self.follower,
                user=self.followed,
                verb="te ha seguido",
                target_type="follow",
            )
            send_ws_notification(self.followed, notif)