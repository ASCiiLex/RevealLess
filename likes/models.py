from django.db import models
from django.contrib.auth.models import User
from posts.models import Post


class PostReaction(models.Model):
    REACTION_CHOICES = [
        ("me_gusta", "Me gusta"),
        ("me_encanta", "Me encanta"),
        ("me_divierte", "Me divierte"),
        ("me_sorprende", "Me sorprende"),
        ("me_enfada", "Me enfada"),
        ("me_da_asco", "Me da asco"),
        ("me_entristece", "Me entristece"),
        ("me_entusiasma", "Me entusiasma"),
        ("me_emociona", "Me emociona"),
        ("me_da_curiosidad", "Me da curiosidad"),
        ("me_da_miedo", "Me da miedo"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="post_reactions", verbose_name='Usuario',
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reactions", verbose_name='Publicación')
    reaction = models.CharField(
        max_length=20, choices=REACTION_CHOICES, default="me_gusta", verbose_name='Reacción',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')

    class Meta:
        unique_together = ("user", "post")
        verbose_name = "Reacción a publicación"
        verbose_name_plural = "Reacciones a publicaciones"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f'{self.user.username} reaccionó "{self.reaction}" al post {self.post.id}'
        )

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
                reaction=self.reaction,
            ).exists():

                notif = Notification.objects.create(
                    user=self.post.author,
                    actor=self.user,
                    verb="reacted",
                    target_type="post",
                    target_id=self.post.id,
                    reaction=self.reaction,
                )

                send_ws_notification(self.post.author, notif)