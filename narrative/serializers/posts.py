from rest_framework import serializers

from posts.models import Post
from .unidades import UnidadNarrativaSerializer

AVATAR_POR_DEFECTO = '/static/img/default_profile.jpg'


class PostSerializer(serializers.ModelSerializer):
    autor = serializers.CharField(source='author.username', read_only=True)
    autor_avatar = serializers.SerializerMethodField()
    obra_titulo = serializers.CharField(source='obra.titulo', read_only=True)
    obra_slug = serializers.CharField(source='obra.slug', read_only=True)
    obra_cruzada = serializers.SerializerMethodField()
    imagen = serializers.SerializerMethodField()
    imagenes = serializers.SerializerMethodField()
    personajes_comparados = serializers.SerializerMethodField()
    referencia_narrativa = UnidadNarrativaSerializer(read_only=True)
    frontera_spoiler = UnidadNarrativaSerializer(read_only=True)
    frontera_cruzada = UnidadNarrativaSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    user_reaction = serializers.SerializerMethodField()
    is_own_post = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'autor', 'autor_avatar', 'obra_titulo', 'obra_slug', 'obra_cruzada', 'text',
            'imagen', 'imagenes', 'disposicion', 'personajes_comparados',
            'referencia_narrativa', 'frontera_spoiler', 'frontera_cruzada', 'nivel_spoiler',
            'emocion_autor', 'created_at',
            'likes_count', 'comments_count', 'user_reaction', 'is_own_post', 'is_saved',
        ]

    def _usuario(self):
        request = self.context.get('request')
        return request.user if request and request.user.is_authenticated else None

    def _cacheado(self, clave, calcular):
        """Una sola consulta por petición, compartida entre todos los posts serializados."""
        if clave not in self.context:
            self.context[clave] = calcular()
        return self.context[clave]

    def get_obra_cruzada(self, obj):
        if not obj.obra_cruzada_id:
            return None
        return {'titulo': obj.obra_cruzada.titulo, 'slug': obj.obra_cruzada.slug}

    def get_imagen(self, obj):
        return obj.image_url

    def get_imagenes(self, obj):
        """Lista única para pintar: la galería si existe; si no, la imagen simple."""
        galeria = [{'url': i.image_url, 'etiqueta': i.etiqueta} for i in obj.imagenes.all() if i.image_url]
        if galeria:
            return galeria
        return [{'url': obj.image_url, 'etiqueta': ''}] if obj.image_url else []

    def get_personajes_comparados(self, obj):
        return [
            {'id': c.personaje_id, 'nombre': c.personaje.nombre, 'imagen_url': c.personaje.image_url}
            for c in obj.comparaciones.all()
        ]

    def get_autor_avatar(self, obj):
        return obj.author.profile.image_url if hasattr(obj.author, 'profile') else AVATAR_POR_DEFECTO

    def get_user_reaction(self, obj):
        usuario = self._usuario()
        if not usuario:
            return None
        from likes.models import PostReaction
        reaccion_por_post = self._cacheado('_user_reactions', lambda: dict(
            PostReaction.objects.filter(user=usuario).values_list('post_id', 'reaction')
        ))
        return reaccion_por_post.get(obj.id)

    def get_is_own_post(self, obj):
        usuario = self._usuario()
        return usuario is not None and usuario == obj.author

    def get_is_saved(self, obj):
        usuario = self._usuario()
        if not usuario:
            return False
        from saved_posts.models import SavedPost
        ids_guardados = self._cacheado('_saved_post_ids', lambda: set(
            SavedPost.objects.filter(user=usuario).values_list('post_id', flat=True)
        ))
        return obj.id in ids_guardados