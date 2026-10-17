from django.db.models.query import QuerySet
from rest_framework import serializers

from core.reacciones import totales_agrupados, totales_de
from posts.models import Post, PostImagen
from ..services.personajes import presentacion_personaje
from .unidades import UnidadNarrativaSerializer

AVATAR_POR_DEFECTO = '/static/img/default_profile.jpg'


class PostSerializer(serializers.ModelSerializer):
    autor = serializers.CharField(source='author.username', read_only=True)
    autor_avatar = serializers.SerializerMethodField()
    obra_titulo = serializers.CharField(source='obra.titulo', read_only=True)
    obra_slug = serializers.CharField(source='obra.slug', read_only=True)
    obra_cruzada = serializers.SerializerMethodField()
    temas = serializers.SerializerMethodField()
    imagen = serializers.SerializerMethodField()
    imagenes = serializers.SerializerMethodField()
    personajes_comparados = serializers.SerializerMethodField()
    referencia_narrativa = UnidadNarrativaSerializer(read_only=True)
    frontera_spoiler = UnidadNarrativaSerializer(read_only=True)
    frontera_cruzada = UnidadNarrativaSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    reacciones_totales = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()
    is_own_post = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'autor', 'autor_avatar', 'obra_titulo', 'obra_slug', 'obra_cruzada', 'modo_cruce',
            'temas', 'text', 'imagen', 'imagenes', 'disposicion', 'personajes_comparados',
            'referencia_narrativa', 'frontera_spoiler', 'frontera_cruzada', 'nivel_spoiler',
            'emocion_autor', 'created_at',
            'likes_count', 'comments_count', 'reacciones_totales', 'user_reaction', 'is_own_post', 'is_saved',
        ]

    def _usuario(self):
        request = self.context.get('request')
        return request.user if request and request.user.is_authenticated else None

    def _cacheado(self, clave, calcular):
        """Una sola consulta por petición, compartida entre todos los posts serializados."""
        if clave not in self.context:
            self.context[clave] = calcular()
        return self.context[clave]

    def _ids_de_la_lista(self, obj):
        """Ids de todos los posts de la lista que se está serializando; fuera de una lista, solo este."""
        lista = self.parent.instance if isinstance(self.parent, serializers.ListSerializer) else None
        if isinstance(lista, (list, tuple, QuerySet)):
            return [p.id for p in lista]
        return [obj.id]

    def get_obra_cruzada(self, obj):
        if not obj.obra_cruzada_id:
            return None
        return {'titulo': obj.obra_cruzada.titulo, 'slug': obj.obra_cruzada.slug}

    def get_temas(self, obj):
        return [{'id': t.id, 'nombre': t.nombre} for t in obj.temas_transversales.all()]

    def get_imagen(self, obj):
        return obj.image_url

    def get_imagenes(self, obj):
        """Lista única para pintar: la galería (con su encuadre) si existe; si no, la imagen simple."""
        galeria = [
            {
                'url': i.image_url, 'etiqueta': i.etiqueta,
                'enfoque_x': i.enfoque_x, 'enfoque_y': i.enfoque_y, 'zoom': i.zoom,
            }
            for i in obj.imagenes.all() if i.image_url
        ]
        if galeria:
            return galeria
        if not obj.image_url:
            return []
        return [{
            'url': obj.image_url, 'etiqueta': '',
            'enfoque_x': PostImagen.ENFOQUE_CENTRO, 'enfoque_y': PostImagen.ENFOQUE_CENTRO,
            'zoom': PostImagen.ZOOM_BASE,
        }]

    def get_personajes_comparados(self, obj):
        """Nombre e imagen según la frontera del post: quien puede leerlo ya llegó ahí,
        así que se muestra lo revelado hasta ese punto y nada posterior."""
        progreso = {obj.obra_id: obj.frontera_orden or 0}
        if obj.obra_cruzada_id:
            progreso[obj.obra_cruzada_id] = obj.frontera_cruzada_orden or 0
        resultado = []
        for c in obj.comparaciones.all():
            if c.personaje_id:
                datos = presentacion_personaje(c.personaje, progreso)
                resultado.append({
                    'id': c.personaje_id, 'nombre': datos['nombre'],
                    'imagen_url': datos['imagen_url'], 'pendiente': False,
                })
            elif c.solicitud_id:
                # Propuesto por el autor: visible con su nombre mientras se revisa.
                resultado.append({'id': None, 'nombre': c.solicitud.nombre, 'imagen_url': None, 'pendiente': True})
        return resultado

    def get_autor_avatar(self, obj):
        return obj.author.profile.image_url if hasattr(obj.author, 'profile') else AVATAR_POR_DEFECTO

    def get_reacciones_totales(self, obj):
        """Totales por emoción de todos los posts de la lista en una consulta agrupada:
        cada tarjeta ya no tiene que pedirlos por separado."""
        from likes.models import PostReaction
        claves = tuple(c for c, _ in PostReaction.REACTION_CHOICES)
        cache = self.context.setdefault('_reacciones_totales', {'ids': set(), 'totales': {}})
        if obj.id not in cache['ids']:
            ids = self._ids_de_la_lista(obj)
            cache['totales'].update(
                totales_agrupados(PostReaction.objects.filter(post_id__in=ids), 'post_id', claves)
            )
            cache['ids'].update(ids)
        return totales_de(cache['totales'], obj.id, claves)

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