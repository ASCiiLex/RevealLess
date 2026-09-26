import math

from rest_framework import serializers
from posts.models import Post
from .models import UnidadNarrativa, ProgresoUsuario, Obra, SolicitudTema


def calcular_progreso_pct(orden_absoluto, longitud_total):
    """Nunca redondea hacia arriba hasta el 100% salvo que el progreso
    sea matemáticamente exacto: mostrar "100%" cuando de verdad quedan
    episodios pendientes contradice el proposito anti-spoiler (podria
    dar al usuario una falsa sensacion de estar al dia). Se usa floor,
    con la excepcion explicita del caso realmente completo (evita el
    error opuesto: mostrar "99%" para quien si termino del todo)."""
    if not longitud_total:
        return None
    ratio = orden_absoluto / longitud_total
    if ratio >= 1:
        pct = 100
    else:
        pct = math.floor(ratio * 100)
    return min(max(pct, 0), 100)


class UnidadNarrativaSerializer(serializers.ModelSerializer):
    imagen = serializers.SerializerMethodField()
    padre = serializers.IntegerField(source='padre_id', read_only=True, allow_null=True)
    padre_etiqueta = serializers.SerializerMethodField()

    class Meta:
        model = UnidadNarrativa
        fields = [
            'id',
            'nombre',
            'tipo',
            'etiqueta',
            'orden_inicio',
            'orden_fin',
            'imagen',
            'padre',
            'padre_etiqueta',
        ]

    def get_imagen(self, obj):
        return obj.image_url

    def get_padre_etiqueta(self, obj):
        return obj.padre.etiqueta if obj.padre_id else None


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
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'autor', 'autor_avatar', 'obra_titulo', 'obra_slug', 'text', 'imagen',
            'referencia_narrativa', 'frontera_spoiler', 'nivel_spoiler', 'emocion_autor', 'created_at',
            'likes_count', 'comments_count', 'user_reaction', 'is_own_post', 'is_saved',
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

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        # Una sola consulta por petición: el conjunto de ids se cachea en el contexto compartido.
        ids_guardados = self.context.get('_saved_post_ids')
        if ids_guardados is None:
            from saved_posts.models import SavedPost
            ids_guardados = set(
                SavedPost.objects.filter(user=request.user).values_list('post_id', flat=True)
            )
            self.context['_saved_post_ids'] = ids_guardados
        return obj.id in ids_guardados


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
        orden_absoluto = progreso_por_obra[obj.id]
        return calcular_progreso_pct(orden_absoluto, longitud_total)

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
        if not progreso:
            return None
        return calcular_progreso_pct(progreso.orden_absoluto, longitud_total)

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


class TemaLomoSerializer(serializers.Serializer):
    """Representa un TemaTransversal suscrito como si fuera un LomoObra
    en el carrusel: mismo shape que ObraResumenSerializer (id, titulo,
    slug, imagen_url, categorias, suscrito, suscripcion_id), sin
    progreso_pct -- un tema no tiene progreso propio, siempre vive a
    nivel de obra. 'slug' apunta al slug de la obra dueña del tema (para
    reutilizar el mismo link de icono 'i' -> landing). 'id' se invierte
    a negativo: los PKs de TemaTransversal y Obra son autoincrementales
    de tablas distintas y colisionan con normalidad (mismo id numerico
    para un tema y una obra), lo que corrompe las keys de React y el
    filtro por obraFiltro en el carrusel -- el id real para
    enlazar/suscribir sigue disponible en tema_id."""

    id = serializers.SerializerMethodField()
    titulo = serializers.CharField(source='nombre')
    slug = serializers.CharField(source='obra.slug')
    imagen_url = serializers.SerializerMethodField()
    categorias = serializers.SerializerMethodField()
    suscrito = serializers.SerializerMethodField()
    suscripcion_id = serializers.SerializerMethodField()
    es_tema = serializers.SerializerMethodField()
    tema_id = serializers.IntegerField(source='id')

    def get_id(self, obj):
        return -obj.id

    def get_imagen_url(self, obj):
        return obj.image_url

    def get_categorias(self, obj):
        return ['Temas']

    def get_suscrito(self, obj):
        return True  # solo se listan temas ya suscritos

    def get_suscripcion_id(self, obj):
        return self.context.get('suscripcion_id_por_tema', {}).get(obj.id)

    def get_es_tema(self, obj):
        return True