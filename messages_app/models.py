from django.db import models
from django.contrib.auth.models import User


class Message(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # NUEVO: para saber si el receptor lo ha leído
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}"


class MessageReaction(models.Model):
    """Mismo catálogo de 11 emociones que PostReaction/CommentReaction.
    Solo el remitente o el destinatario del mensaje pueden reaccionar
    (verificado en la vista, no aquí) -- una reacción a un mensaje
    ajeno a la conversación no tiene sentido."""

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
        User, on_delete=models.CASCADE, related_name="message_reactions"
    )
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="reactions"
    )
    reaction = models.CharField(max_length=20, choices=REACTION_CHOICES, default="me_gusta")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "message")
        ordering = ["-created_at"]

    def __str__(self):
        return f'{self.user.username} reaccionó "{self.reaction}" al mensaje {self.message.id}'