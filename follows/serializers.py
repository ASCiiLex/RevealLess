from rest_framework import serializers
from .models import Follow


class FollowToggleSerializer(serializers.Serializer):
    is_following = serializers.BooleanField()