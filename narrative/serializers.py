from rest_framework import serializers
from posts.models import Post
from .models import UnidadNarrativa, ProgresoUsuario, Obra


class UnidadNarrativaSerializer(serializers.ModelSerializer):
    imagen = serializers.SerializerMethodField()

    class Meta:
        model = UnidadNarrativa
        fields = ['id', 'nombre', 'tipo', 'etiqueta', 'orden_inicio', 'orden_fin', 'imagen']

    def get_imagen(self, obj):
        return obj.image_url


class ProgresoUsuarioSerializer(serializers.ModelSerializer):
    unidad_actual = UnidadNarrativaSerializer(read_only=True)

    class Meta:
        model = ProgresoUsuario
        fields = ['unidad_actual', 'orden_absoluto']


class PostSerializer(serializers.ModelSerializer):
    autor = serializers.CharField(source='author.username', read_only=True)
    obra_titulo = serializers.CharField(source='obra.titulo', read_only=True)
    obra_slug = serializers.CharField(source='obra.slug', read_only=True)
    imagen = serializers.SerializerMethodField()
    referencia_narrativa = UnidadNarrativaSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'autor', 'obra_titulo', 'obra_slug', 'text', 'imagen',
            'referencia_narrativa', 'nivel_spoiler', 'created_at',
            'likes_count', 'comments_count',
        ]

    def get_imagen(self, obj):
        return obj.image_url


class ObraResumenSerializer(serializers.ModelSerializer):
    """Vista ligera de Obra para el carrusel biblioteca/descubrir. No
    incluye progreso ni unidades: si el frontend necesita ese detalle,
    lo pide aparte vía narrative/api/progreso/<slug>/."""

    imagen_url = serializers.SerializerMethodField()
    categorias = serializers.SlugRelatedField(many=True, read_only=True, slug_field='nombre')

    class Meta:
        model = Obra
        fields = ['id', 'titulo', 'slug', 'imagen_url', 'categorias']

    def get_imagen_url(self, obj):
        return obj.image_url