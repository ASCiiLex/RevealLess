from rest_framework import serializers
from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'text', 'created_at']


class InboxItemSerializer(serializers.Serializer):
    username = serializers.CharField()
    avatar = serializers.CharField()
    last_message = serializers.CharField()
    unread_count = serializers.IntegerField()