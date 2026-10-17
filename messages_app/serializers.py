from rest_framework import serializers
from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.username', read_only=True)
    reaccion = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'text', 'created_at', 'reaccion']

    def get_reaccion(self, obj):
        """La del destinatario, la única que cuenta (se ignoran las antiguas del remitente).
        Usa las reacciones precargadas: sin consulta por mensaje."""
        return next((r.reaction for r in obj.reactions.all() if r.user_id == obj.receiver_id), None)


class InboxItemSerializer(serializers.Serializer):
    username = serializers.CharField()
    avatar = serializers.CharField()
    last_message = serializers.CharField()
    unread_count = serializers.IntegerField()