import math

from rest_framework import serializers

from core.imagenes.miniaturas import url_variante
from ..models import Obra, RelevanciaPersonaje
from ..services.personajes import presentacion_personaje
from .temas import CarruselMixin, TemaConSuscripcionSerializer

R = RelevanciaPersonaje
# Chips del carrusel: tres grupos que caben en una fila en móvil; el orden interno sigue usando los cinco niveles.
GRUPOS_RELEVANCIA = [
    ('principales', 'Principales', [R.NIVEL_PROTAGONISTA, R.NIVEL_PRINCIPAL]),
    ('destacados', 'Destacados', [R.NIVEL_DESTACADO]),
    ('secundarios', 'Secundarios', [R.NIVEL_SECUNDARIO, R.NIVEL_EPISODICO]),
]


def calcular_progreso_pct(orden_absoluto, longitud_total):
    """floor, no round: mostrar 100% con episodios pendientes daría una falsa sensación
    de estar al día. Solo el progreso completo exacto llega a 100."""
    if not longitud_total:
        return None
    ratio = orden_absoluto / longitud_total
    pct = 100 if ratio >= 1 else math.floor(ratio * 100)
    return min(max(pct, 0), 100)


class ObraSuscripcionMixin(CarruselMixin):
    """Imagen, categorías y estado de la suscripción a la obra completa, a partir del contexto de la vista."""

    categorias = serializers.SlugRelatedField(many=True, read_only=True, slug_field='nombre')

    def get_suscrito(self, obj):
        return obj.id in (self.context.get('ids_obras_suscritas') or set())

    def get_suscripcion_id(self, obj):
        return (self.context.get('suscripcion_id_por_obra') or {}).get(obj.id)

    def get_silenciada(self, obj):
        return obj.id in (self.context.get('ids_obras_silenciadas') or set())


class ObraResumenSerializer(ObraSuscripcionMixin, serializers.ModelSerializer):
    clave = serializers.SerializerMethodField()
    progreso_pct = serializers.SerializerMethodField()

    class Meta:
        model = Obra
        fields = [
            'id', 'clave', 'titulo', 'slug', 'imagen_url', 'categorias',
            'progreso_pct', 'suscrito', 'suscripcion_id', 'silenciada',
        ]

    def get_clave(self, obj):
        return f'obra-{obj.id}'

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
    grupos_relevancia = serializers.SerializerMethodField()

    class Meta:
        model = Obra
        fields = [
            'id', 'titulo', 'slug', 'sinopsis', 'imagen_url', 'categorias', 'categorias_detalle',
            'suscrito', 'suscripcion_id', 'silenciada', 'progreso_pct', 'total_suscriptores', 'temas',
            'obras_relacionadas', 'personajes', 'grupos_relevancia',
        ]

    def get_imagen_url(self, obj):
        # Cabecera de la landing: se pinta grande, con la variante de 900 px.
        return url_variante(obj.imagen, 'med') or obj.imagen_por_defecto

    def get_progreso_pct(self, obj):
        progreso = self.context.get('progreso')
        if not progreso:
            return None
        return calcular_progreso_pct(progreso.orden_absoluto, self.context.get('longitud_total'))

    def get_total_suscriptores(self, obj):
        return self.context.get('total_suscriptores', 0)

    def get_temas(self, obj):
        # La vista ya filtra por visibilidad: aquí no se listan temas por su cuenta.
        suscripcion_id_por_tema = self.context.get('suscripcion_id_por_tema', {})
        return TemaConSuscripcionSerializer([
            {
                'id': t.id,
                'nombre': t.nombre,
                'suscrito': t.id in suscripcion_id_por_tema,
                'suscripcion_id': suscripcion_id_por_tema.get(t.id),
            }
            for t in self.context.get('temas_visibles', [])
        ], many=True).data

    def get_categorias_detalle(self, obj):
        return [{'id': c.id, 'nombre': c.nombre} for c in obj.categorias.all()]

    def get_obras_relacionadas(self, obj):
        return [{'id': o.id, 'titulo': o.titulo, 'slug': o.slug} for o in obj.obras_relacionadas()]

    def get_personajes(self, obj):
        # La vista ya filtra por progreso y ordena; aquí solo la etapa visible y el nivel para los chips.
        suscripciones = self.context.get('suscripcion_id_por_personaje', {})
        progreso = self.context.get('progreso_por_obra', {})
        return [
            {
                'id': p.id,
                **presentacion_personaje(p, progreso, obra_id=obj.id),
                'nivel': getattr(p, 'nivel_relevancia', R.NIVEL_SIN_MARCAR),
                'suscripcion_id': suscripciones.get(p.id),
            }
            for p in self.context.get('personajes_visibles', [])
        ]

    def get_grupos_relevancia(self, obj):
        return [
            {
                'clave': clave,
                'nombre': nombre,
                'niveles': niveles,
                'por_defecto': max(niveles) >= R.NIVEL_MINIMO_POR_DEFECTO,
            }
            for clave, nombre, niveles in GRUPOS_RELEVANCIA
        ]