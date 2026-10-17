from rest_framework import serializers

from core.reacciones import totales_de
from narrative.models import ClasificacionNarrativa, Obra, UnidadNarrativa
from .models import CommentReaction


EMOCION_CHOICES = [c[0] for c in ClasificacionNarrativa.EMOCION_CHOICES]
CLAVES_REACCION = tuple(c for c, _ in CommentReaction.REACTION_CHOICES)


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
    obra_cruzada = serializers.PrimaryKeyRelatedField(
        queryset=Obra.objects.all(), required=False, allow_null=True
    )
    frontera_cruzada = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True
    )
    descartar_referencia_cruzada = serializers.BooleanField(required=False, default=False)


class CommentUpdateSerializer(serializers.Serializer):
    """Edición de un comentario ya publicado, mismo criterio que
    PostUpdateSerializer: todos los campos opcionales, sin detección de
    referencia cruzada (solo se dispara al crear)."""

    text = serializers.CharField(max_length=2000, required=False)
    emocion_autor = serializers.ChoiceField(choices=EMOCION_CHOICES, required=False, allow_null=True)
    referencia_narrativa = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False
    )
    frontera_spoiler = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True
    )
    obra_cruzada = serializers.PrimaryKeyRelatedField(
        queryset=Obra.objects.all(), required=False, allow_null=True
    )
    frontera_cruzada = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True
    )


class CommentSerializer(serializers.Serializer):
    """Recursivo: cada reply se serializa con el mismo serializer, compartiendo el context
    (reaction_map y reacciones_totales) para no repetir consultas en cada nivel de anidación."""

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
    obra_cruzada_id = serializers.IntegerField(allow_null=True)
    frontera_cruzada_id = serializers.IntegerField(allow_null=True)
    is_own_comment = serializers.SerializerMethodField()
    reactions_count = serializers.SerializerMethodField()
    reacciones_totales = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    def _totales(self, obj):
        """Precalculados en la vista; sin ellos (otros usos del serializer), None."""
        if 'reacciones_totales' not in self.context:
            return None
        return totales_de(self.context['reacciones_totales'], obj.id, CLAVES_REACCION)

    def get_avatar(self, obj):
        return obj.user.profile.image_url if hasattr(obj.user, 'profile') else '/static/img/default_profile.jpg'

    def get_is_own_comment(self, obj):
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and request.user == obj.user)

    def get_reactions_count(self, obj):
        totales = self._totales(obj)
        return sum(totales.values()) if totales is not None else obj.reactions.count()

    def get_reacciones_totales(self, obj):
        return self._totales(obj)

    def get_user_reaction(self, obj):
        reaction_map = self.context.get('reaction_map', {})
        return reaction_map.get(obj.id)

    def get_replies(self, obj):
        return CommentSerializer(obj.replies.all(), many=True, context=self.context).data