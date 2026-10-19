from rest_framework import serializers

from ..services.personajes import presentacion_personaje
from .temas import CarruselMixin


class PersonajeLomoSerializer(CarruselMixin):
    """Personaje suscrito como lomo: nombre e imagen según el progreso, igual que su landing
    sin obra de contexto. Espera progreso_por_obra en el contexto y prefetch de etapas."""

    id = serializers.IntegerField()
    clave = serializers.SerializerMethodField()
    titulo = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    categorias = serializers.SerializerMethodField()
    es_personaje = serializers.SerializerMethodField()
    personaje_id = serializers.IntegerField(source='id')

    def _presentacion(self, obj):
        cache = self.context.setdefault('_presentaciones', {})
        if obj.id not in cache:
            cache[obj.id] = presentacion_personaje(obj, self.context.get('progreso_por_obra', {}))
        return cache[obj.id]

    def get_clave(self, obj):
        return f'personaje-{obj.id}'

    def get_titulo(self, obj):
        return self._presentacion(obj)['nombre']

    def get_imagen_url(self, obj):
        return self._presentacion(obj)['imagen_url']

    def get_slug(self, obj):
        return ''

    def get_categorias(self, obj):
        return ['Personajes']

    def get_suscrito(self, obj):
        return True  # solo se listan personajes ya suscritos

    def get_suscripcion_id(self, obj):
        return self.context.get('suscripcion_id_por_personaje', {}).get(obj.id)

    def get_silenciada(self, obj):
        return obj.id in self.context.get('ids_personajes_silenciados', set())

    def get_es_personaje(self, obj):
        return True