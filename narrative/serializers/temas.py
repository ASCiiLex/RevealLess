from rest_framework import serializers

from ..models import SolicitudTema


class CarruselMixin(serializers.Serializer):
    """Campos comunes a todo lo que se muestra como lomo en el carrusel (obras y temas)."""

    imagen_url = serializers.SerializerMethodField()
    suscrito = serializers.SerializerMethodField()
    suscripcion_id = serializers.SerializerMethodField()

    def get_imagen_url(self, obj):
        return obj.image_url


class TemaConSuscripcionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    suscrito = serializers.BooleanField()
    suscripcion_id = serializers.IntegerField(allow_null=True)


class TemaLomoSerializer(CarruselMixin):
    """TemaTransversal suscrito con el mismo formato que ObraResumenSerializer, sin progreso_pct.
    'slug' es el de la obra dueña (enlace a su landing). 'id' va en negativo porque los PK
    de temas y obras colisionan y rompen las keys de React; el id real está en tema_id."""

    id = serializers.SerializerMethodField()
    titulo = serializers.CharField(source='nombre')
    slug = serializers.CharField(source='obra.slug')
    categorias = serializers.SerializerMethodField()
    es_tema = serializers.SerializerMethodField()
    tema_id = serializers.IntegerField(source='id')

    def get_id(self, obj):
        return -obj.id

    def get_categorias(self, obj):
        return ['Temas']

    def get_suscrito(self, obj):
        return True  # solo se listan temas ya suscritos

    def get_suscripcion_id(self, obj):
        return self.context.get('suscripcion_id_por_tema', {}).get(obj.id)

    def get_es_tema(self, obj):
        return True


class SolicitudTemaSerializer(serializers.ModelSerializer):
    obra_titulo = serializers.CharField(source='obra.titulo', read_only=True)

    class Meta:
        model = SolicitudTema
        fields = ['id', 'obra', 'obra_titulo', 'nombre', 'estado', 'creado_en', 'resuelto_en']
        read_only_fields = ['estado', 'creado_en', 'resuelto_en']