from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Réplica de los datos que ya expone Notification vía sus
    @property (avatar, url) -- no se recalculan aquí, se reutilizan
    directamente para no duplicar esa lógica de negocio."""

    actor = serializers.CharField(source='actor.username', read_only=True)
    avatar = serializers.CharField(read_only=True)
    url = serializers.CharField(read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'actor', 'avatar', 'verb', 'url', 'created_at', 'seen']