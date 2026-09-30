import math

from rest_framework import serializers

from ..models import Obra
from .temas import CarruselMixin, TemaConSuscripcionSerializer


def calcular_progreso_pct(orden_absoluto, longitud_total):
    """floor, no round: mostrar 100% con episodios pendientes daría una falsa sensación
    de estar al día. Solo el progreso completo exacto llega a 100."""
    if not longitud_total:
        return None
    ratio = orden_absoluto / longitud_total
    pct = 100 if ratio >= 1 else math.floor(ratio * 100)
    return min(max(pct, 0), 100)


class ObraSuscripcionMixin(CarruselMixin):
    """Imagen, categorías y estado de suscripción de una obra, a partir del contexto de la vista."""

    categorias = serializers.SlugRelatedField(many=True, read_only=True, slug_field='nombre')

    def get_suscrito(self, obj):
        return obj.id in (self.context.get('ids_obras_suscritas') or set())

    def get_suscripcion_id(self, obj):
        return (self.context.get('suscripcion_id_por_obra') or {}).get(obj.id)


class ObraResumenSerializer(ObraSuscripcionMixin, serializers.ModelSerializer):
    progreso_pct = serializers.SerializerMethodField()

    class Meta:
        model = Obra
        fields = [
            'id', 'titulo', 'slug', 'imagen_url', 'categorias',
            'progreso_pct', 'suscrito', 'suscripcion_id',
        ]

    def get_progreso_pct(self, obj):
        progreso_por_obra = self.context.get('progreso_por_obra') or {}
        if obj.id not in progreso_por_obra:
            return None
        return calcular_progreso_pct(progreso_por_obra[obj.id], getattr(obj, 'longitud_total', None))


class ObraLandingSerializer(ObraSuscripcionMixin, serializers.ModelSerializer):
    """Landing de obra: catálogo, progreso, suscriptores, temas, relaciones y personajes."""

    progreso_pct = serializers.SerializerMethodField()
    total_suscriptores = serializers.SerializerMethodField()
    temas = serializers.SerializerMethodField()
    categorias_detalle = serializers.SerializerMethodField()
    obras_relacionadas = serializers.SerializerMethodField()
    personajes = serializers.SerializerMethodField()

    class Meta:
        model = Obra
        fields = [
            'id', 'titulo', 'slug', 'sinopsis', 'imagen_url', 'categorias', 'categorias_detalle',
            'suscrito', 'suscripcion_id', 'progreso_pct', 'total_suscriptores', 'temas',
            'obras_relacionadas', 'personajes',
        ]

    def get_progreso_pct(self, obj):
        progreso = self.context.get('progreso')
        if not progreso:
            return None
        return calcular_progreso_pct(progreso.orden_absoluto, self.context.get('longitud_total'))

    def get_total_suscriptores(self, obj):
        return self.context.get('total_suscriptores', 0)

    def get_temas(self, obj):
        suscripcion_id_por_tema = self.context.get('suscripcion_id_por_tema', {})
        return TemaConSuscripcionSerializer([
            {
                'id': t.id,
                'nombre': t.nombre,
                'suscrito': t.id in suscripcion_id_por_tema,
                'suscripcion_id': suscripcion_id_por_tema.get(t.id),
            }
            for t in obj.temas_transversales.all().order_by('nombre')
        ], many=True).data

    def get_categorias_detalle(self, obj):
        return [{'id': c.id, 'nombre': c.nombre} for c in obj.categorias.all()]

    def get_obras_relacionadas(self, obj):
        return [{'id': o.id, 'titulo': o.titulo, 'slug': o.slug} for o in obj.obras_relacionadas()]

    def get_personajes(self, obj):
        # La vista ya filtra por progreso: aquí solo se da forma.
        suscripciones = self.context.get('suscripcion_id_por_personaje', {})
        return [
            {
                'id': p.id,
                'nombre': p.nombre,
                'imagen_url': p.image_url,
                'suscripcion_id': suscripciones.get(p.id),
            }
            for p in self.context.get('personajes_visibles', [])
        ]