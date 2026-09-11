from rest_framework import serializers
from narrative.models import Obra, UnidadNarrativa, TemaTransversal
from .models import Suscripcion
from .services import posts_no_leidos_count


class ObraMiniSerializer(serializers.ModelSerializer):
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Obra
        fields = ['id', 'titulo', 'slug', 'imagen_url']

    def get_imagen_url(self, obj):
        return obj.image_url


class UnidadMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadNarrativa
        fields = ['id', 'etiqueta']


class TemaMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemaTransversal
        fields = ['id', 'nombre']


class SuscripcionSerializer(serializers.ModelSerializer):
    obra = ObraMiniSerializer(read_only=True)
    unidad = UnidadMiniSerializer(read_only=True)
    tema = TemaMiniSerializer(read_only=True)
    nivel = serializers.CharField(read_only=True)
    no_leidos = serializers.SerializerMethodField()

    class Meta:
        model = Suscripcion
        fields = ['id', 'obra', 'unidad', 'tema', 'nivel', 'no_leidos', 'ultima_visita']

    def get_no_leidos(self, obj):
        return posts_no_leidos_count(obj)


class SuscripcionCreateSerializer(serializers.Serializer):
    """Serializer de entrada para crear una suscripcion. No usa
    ModelSerializer porque la validacion cruzada (unidad y tema son
    mutuamente excluyentes, ambos deben pertenecer a la obra) ya vive en
    crear_suscripcion()/Suscripcion.clean() — este serializer solo valida
    la forma de los datos, no las reglas de dominio."""

    obra = serializers.SlugRelatedField(slug_field='slug', queryset=Obra.objects.all())
    unidad = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True
    )
    tema = serializers.PrimaryKeyRelatedField(
        queryset=TemaTransversal.objects.all(), required=False, allow_null=True
    )