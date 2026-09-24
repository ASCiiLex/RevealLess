from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Expone avatar, url y verbo traducido reutilizando las @property
    de Notification, sin duplicar esa lógica."""

    actor = serializers.CharField(source='actor.username', read_only=True)
    avatar = serializers.CharField(read_only=True)
    url = serializers.CharField(read_only=True)
    verb = serializers.CharField(source='verb_display', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'actor', 'avatar', 'verb', 'url', 'created_at', 'seen']