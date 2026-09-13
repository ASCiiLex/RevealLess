from rest_framework import serializers


class CommentSerializer(serializers.Serializer):
    """Recursivo: cada reply se serializa con el mismo serializer,
    compartiendo el context (reaction_map) para no repetir la consulta
    de reacciones del usuario en cada nivel de anidación."""

    id = serializers.IntegerField()
    user = serializers.CharField(source='user.username')
    avatar = serializers.SerializerMethodField()
    text = serializers.CharField()
    created_at = serializers.DateTimeField()
    parent_id = serializers.IntegerField(allow_null=True)
    reactions_count = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    def get_avatar(self, obj):
        return obj.user.profile.image_url if hasattr(obj.user, 'profile') else '/static/img/default_profile.jpg'

    def get_reactions_count(self, obj):
        return obj.reactions.count()

    def get_user_reaction(self, obj):
        reaction_map = self.context.get('reaction_map', {})
        return reaction_map.get(obj.id)

    def get_replies(self, obj):
        return CommentSerializer(obj.replies.all(), many=True, context=self.context).data