from rest_framework import serializers
from posts.models import Post
from .models import UnidadNarrativa, ProgresoUsuario, Obra, SolicitudTema


class UnidadNarrativaSerializer(serializers.ModelSerializer):
    imagen = serializers.SerializerMethodField()
    padre = serializers.IntegerField(source='padre_id', read_only=True, allow_null=True)

    class Meta:
        model = UnidadNarrativa
        fields = ['id', 'nombre', 'tipo', 'etiqueta', 'orden_inicio', 'orden_fin', 'imagen', 'padre']

    def get_imagen(self, obj):
        return obj.image_url


class ProgresoUsuarioSerializer(serializers.ModelSerializer):
    unidad_actual = UnidadNarrativaSerializer(read_only=True)

    class Meta:
        model = ProgresoUsuario
        fields = ['unidad_actual', 'orden_absoluto']


class PostSerializer(serializers.ModelSerializer):
    autor = serializers.CharField(source='author.username', read_only=True)
    autor_avatar = serializers.SerializerMethodField()
    obra_titulo = serializers.CharField(source='obra.titulo', read_only=True)
    obra_slug = serializers.CharField(source='obra.slug', read_only=True)
    imagen = serializers.SerializerMethodField()
    referencia_narrativa = UnidadNarrativaSerializer(read_only=True)
    frontera_spoiler = UnidadNarrativaSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    user_reaction = serializers.SerializerMethodField()
    is_own_post = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'autor', 'autor_avatar', 'obra_titulo', 'obra_slug', 'text', 'imagen',
            'referencia_narrativa', 'frontera_spoiler', 'nivel_spoiler', 'created_at',
            'likes_count', 'comments_count', 'user_reaction', 'is_own_post',
        ]

    def get_imagen(self, obj):
        return obj.image_url

    def get_autor_avatar(self, obj):
        return obj.author.profile.image_url if hasattr(obj.author, 'profile') else '/static/img/default_profile.jpg'

    def get_user_reaction(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        from likes.models import PostReaction
        reaction = PostReaction.objects.filter(user=request.user, post=obj).first()
        return reaction.reaction if reaction else None

    def get_is_own_post(self, obj):
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and request.user == obj.author)


class ObraResumenSerializer(serializers.ModelSerializer):
    imagen_url = serializers.SerializerMethodField()
    categorias = serializers.SlugRelatedField(many=True, read_only=True, slug_field='nombre')
    progreso_pct = serializers.SerializerMethodField()
    suscrito = serializers.SerializerMethodField()
    suscripcion_id = serializers.SerializerMethodField()

    class Meta:
        model = Obra
        fields = [
            'id', 'titulo', 'slug', 'imagen_url', 'categorias',
            'progreso_pct', 'suscrito', 'suscripcion_id',
        ]

    def get_imagen_url(self, obj):
        return obj.image_url

    def get_progreso_pct(self, obj):
        progreso_por_obra = self.context.get('progreso_por_obra')
        if not progreso_por_obra or obj.id not in progreso_por_obra:
            return None
        longitud_total = getattr(obj, 'longitud_total', None)
        if not longitud_total:
            return None
        orden_absoluto = progreso_por_obra[obj.id]
        pct = round((orden_absoluto / longitud_total) * 100)
        return min(max(pct, 0), 100)

    def get_suscrito(self, obj):
        return obj.id in (self.context.get('ids_obras_suscritas') or set())

    def get_suscripcion_id(self, obj):
        ids_por_obra = self.context.get('suscripcion_id_por_obra')
        if not ids_por_obra:
            return None
        return ids_por_obra.get(obj.id)


class SolicitudTemaSerializer(serializers.ModelSerializer):
    obra_titulo = serializers.CharField(source='obra.titulo', read_only=True)

    class Meta:
        model = SolicitudTema
        fields = ['id', 'obra', 'obra_titulo', 'nombre', 'estado', 'creado_en', 'resuelto_en']
        read_only_fields = ['estado', 'creado_en', 'resuelto_en']


class TemaConSuscripcionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    suscrito = serializers.BooleanField()
    suscripcion_id = serializers.IntegerField(allow_null=True)


class ObraLandingSerializer(serializers.ModelSerializer):
    """Serializer dedicado a la landing de obra: junta datos que hoy
    viven repartidos en tres endpoints distintos (ObraResumenSerializer
    para catálogo, ObraDetalleAPIView para unidades/temas planos,
    CatalogoObrasAPIView para progreso) en una sola respuesta pensada
    para esta pantalla concreta."""

    imagen_url = serializers.SerializerMethodField()
    categorias = serializers.SlugRelatedField(many=True, read_only=True, slug_field='nombre')
    suscrito = serializers.SerializerMethodField()
    suscripcion_id = serializers.SerializerMethodField()
    progreso_pct = serializers.SerializerMethodField()
    total_suscriptores = serializers.SerializerMethodField()
    temas = serializers.SerializerMethodField()

    class Meta:
        model = Obra
        fields = [
            'id', 'titulo', 'slug', 'sinopsis', 'imagen_url', 'categorias',
            'suscrito', 'suscripcion_id', 'progreso_pct', 'total_suscriptores', 'temas',
        ]

    def get_imagen_url(self, obj):
        return obj.image_url

    def get_suscrito(self, obj):
        return obj.id in (self.context.get('ids_obras_suscritas') or set())

    def get_suscripcion_id(self, obj):
        ids_por_obra = self.context.get('suscripcion_id_por_obra')
        if not ids_por_obra:
            return None
        return ids_por_obra.get(obj.id)

    def get_progreso_pct(self, obj):
        progreso = self.context.get('progreso')
        longitud_total = self.context.get('longitud_total')
        if not progreso or not longitud_total:
            return None
        pct = round((progreso.orden_absoluto / longitud_total) * 100)
        return min(max(pct, 0), 100)

    def get_total_suscriptores(self, obj):
        return self.context.get('total_suscriptores', 0)

    def get_temas(self, obj):
        suscripcion_id_por_tema = self.context.get('suscripcion_id_por_tema', {})
        temas = obj.temas_transversales.all().order_by('nombre')
        return TemaConSuscripcionSerializer([
            {
                'id': t.id,
                'nombre': t.nombre,
                'suscrito': t.id in suscripcion_id_por_tema,
                'suscripcion_id': suscripcion_id_por_tema.get(t.id),
            }
            for t in temas
        ], many=True).data