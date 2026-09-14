from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from posts.models import Post
from notifications.models import Notification
from notifications.utils import send_ws_notification, extract_mentions, extract_hashtags
from narrative.models import ClasificacionNarrativa
from .managers import CommentQuerySet


class Comment(ClasificacionNarrativa, models.Model):
    objects = CommentQuerySet.as_manager()

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    frontera_origen = models.CharField(
        max_length=20,
        choices=ClasificacionNarrativa.ORIGEN_CHOICES,
        default=ClasificacionNarrativa.ORIGEN_HEREDADO_POST,
    )

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(frontera_origen=ClasificacionNarrativa.ORIGEN_HEREDADO_POST, frontera_spoiler__isnull=True)
                    | (~models.Q(frontera_origen=ClasificacionNarrativa.ORIGEN_HEREDADO_POST) & models.Q(frontera_spoiler__isnull=False))
                ),
                name='comment_frontera_consistency',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(obra_cruzada__isnull=True, frontera_cruzada__isnull=True)
                    | (models.Q(obra_cruzada__isnull=False) & models.Q(frontera_cruzada__isnull=False))
                ),
                name='comment_frontera_cruzada_consistency',
            ),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.text[:20]}"

    @property
    def is_reply(self):
        return self.parent is not None

    def clean(self):
        super().clean()
        if self.referencia_narrativa_id and self.referencia_narrativa.obra_id != self.post.obra_id:
            raise ValidationError({'referencia_narrativa': 'Debe pertenecer a la obra del post.'})
        if self.frontera_spoiler_id and self.frontera_spoiler.obra_id != self.post.obra_id:
            raise ValidationError({'frontera_spoiler': 'Debe pertenecer a la obra del post.'})
        if self.obra_cruzada_id:
            if self.obra_cruzada_id == self.post.obra_id:
                raise ValidationError({'obra_cruzada': 'Debe ser una obra distinta a la del post.'})
            if self.frontera_cruzada_id and self.frontera_cruzada.obra_id != self.obra_cruzada_id:
                raise ValidationError({'frontera_cruzada': 'Debe pertenecer a obra_cruzada.'})

    @property
    def frontera_efectiva_orden(self):
        if self.frontera_origen == self.ORIGEN_HEREDADO_POST:
            return self.post.frontera_orden
        return self.frontera_orden

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            usernames = extract_mentions(self.text)
            for username in usernames:
                try:
                    mentioned_user = User.objects.get(username=username)
                    notif = Notification.objects.create(
                        user=mentioned_user,
                        actor=self.user,
                        verb="mentioned",
                        target_type="comment",
                        target_id=self.id,
                    )
                    send_ws_notification(mentioned_user, notif)
                except User.DoesNotExist:
                    pass

            tags = extract_hashtags(self.text)
            if tags:
                from posts.models import Hashtag, PostHashtag

                for tag in tags:
                    hashtag, _ = Hashtag.objects.get_or_create(name=tag)
                    PostHashtag.objects.get_or_create(post=self.post, hashtag=hashtag)

        if is_new and not self.is_reply and self.post.author != self.user:
            notif = Notification.objects.create(
                user=self.post.author,
                actor=self.user,
                verb="commented",
                target_type="post",
                target_id=self.post.id,
            )
            send_ws_notification(self.post.author, notif)

        if is_new and self.is_reply and self.parent.user != self.user:
            notif = Notification.objects.create(
                user=self.parent.user,
                actor=self.user,
                verb="replied",
                target_type="comment",
                target_id=self.parent.id,
            )
            send_ws_notification(self.parent.user, notif)


class CommentReaction(models.Model):
    REACTION_CHOICES = [
        ("like", "Me gusta"),
        ("love", "Me encanta"),
        ("funny", "Me divierte"),
        ("wow", "Me sorprende"),
        ("sad", "Me entristece"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comment_reactions"
    )
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="reactions"
    )
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES, default="like")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "comment")
        ordering = ["-created_at"]

    def __str__(self):
        return f'{self.user.username} reaccionó "{self.reaction}" al comentario {self.comment.id}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and self.comment.user != self.user:
            notif = Notification.objects.create(
                user=self.comment.user,
                actor=self.user,
                verb="reacted",
                target_type="comment",
                target_id=self.comment.id,
                reaction=self.reaction,
            )
            send_ws_notification(self.comment.user, notif)