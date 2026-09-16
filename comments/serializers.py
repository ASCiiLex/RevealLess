from rest_framework import serializers

from narrative.models import ClasificacionNarrativa, UnidadNarrativa


EMOCION_CHOICES = [c[0] for c in ClasificacionNarrativa.EMOCION_CHOICES]


class CommentCreateSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=2000)
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    emocion_autor = serializers.ChoiceField(choices=EMOCION_CHOICES, required=False, allow_null=True)
    referencia_narrativa = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True
    )
    frontera_spoiler = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True
    )


class CommentUpdateSerializer(serializers.Serializer):
    """Edición de un comentario ya publicado, mismo criterio que
    PostUpdateSerializer: todos los campos opcionales, si se envía
    frontera_spoiler se marca ORIGEN_EXPLICITO, si no se envía la
    frontera actual no se toca."""

    text = serializers.CharField(max_length=2000, required=False)
    emocion_autor = serializers.ChoiceField(choices=EMOCION_CHOICES, required=False, allow_null=True)
    referencia_narrativa = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False
    )
    frontera_spoiler = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True
    )


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
    emocion_autor = serializers.CharField(allow_null=True)
    referencia_narrativa_id = serializers.IntegerField(allow_null=True)
    frontera_spoiler_id = serializers.IntegerField(allow_null=True)
    frontera_origen = serializers.CharField()
    is_own_comment = serializers.SerializerMethodField()
    reactions_count = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    def get_avatar(self, obj):
        return obj.user.profile.image_url if hasattr(obj.user, 'profile') else '/static/img/default_profile.jpg'

    def get_is_own_comment(self, obj):
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and request.user == obj.user)

    def get_reactions_count(self, obj):
        return obj.reactions.count()

    def get_user_reaction(self, obj):
        reaction_map = self.context.get('reaction_map', {})
        return reaction_map.get(obj.id)

    def get_replies(self, obj):
        return CommentSerializer(obj.replies.all(), many=True, context=self.context).data