from rest_framework import serializers
from .models import SavedPost


class SavedPostSerializer(serializers.ModelSerializer):
    post_id = serializers.IntegerField(source='post.id', read_only=True)
    image_url = serializers.CharField(source='post.image_url', read_only=True)

    class Meta:
        model = SavedPost
        fields = ['id', 'post_id', 'image_url', 'created_at']