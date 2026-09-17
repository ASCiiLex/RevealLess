from rest_framework import serializers
from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.username', read_only=True)
    user_reaction = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'text', 'created_at', 'user_reaction']

    def get_user_reaction(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        reaction = obj.reactions.filter(user=request.user).first()
        return reaction.reaction if reaction else None


class InboxItemSerializer(serializers.Serializer):
    username = serializers.CharField()
    avatar = serializers.CharField()
    last_message = serializers.CharField()
    unread_count = serializers.IntegerField()