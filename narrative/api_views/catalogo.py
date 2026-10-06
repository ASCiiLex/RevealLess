from django.db.models import Max
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Obra, Personaje, ProgresoUsuario, TemaTransversal, UnidadNarrativa
from ..serializers import ObraResumenSerializer, UnidadNarrativaSerializer
from .comun import (
    contexto_suscripcion_obra,
    ids_biblioteca,
    obra_basica,
    temas_planos,
    temas_suscritos_serializados,
)


class CatalogoObrasAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        progreso_por_obra = dict(
            ProgresoUsuario.objects.filter(usuario=request.user).values_list('obra_id', 'orden_absoluto')
        )
        contexto_suscripcion = contexto_suscripcion_obra(request.user)
        ids = set(progreso_por_obra) | contexto_suscripcion['ids_obras_suscritas']

        todas = Obra.objects.prefetch_related('categorias').annotate(
            longitud_total=Max('unidades__orden_fin')
        )
        contexto = {'progreso_por_obra': progreso_por_obra, **contexto_suscripcion}

        biblioteca = ObraResumenSerializer(
            todas.filter(id__in=ids), many=True, context=contexto,
        ).data

        return Response({
            'biblioteca': biblioteca + temas_suscritos_serializados(request.user),
            'descubrir': ObraResumenSerializer(
                todas.exclude(id__in=ids), many=True, context=contexto,
            ).data,
        })


class ObrasPublicarAPIView(APIView):
    """Selector de publicar: solo obras de la biblioteca del usuario y sus temas."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        ids = ids_biblioteca(request.user)
        obras = Obra.objects.filter(id__in=ids).order_by('titulo')
        temas = TemaTransversal.objects.filter(obra_id__in=ids).select_related('obra').order_by('nombre')

        return Response({
            'obras': [{**obra_basica(o), 'imagen_url': o.image_url} for o in obras],
            'temas': [
                {'id': t.id, 'nombre': t.nombre, 'obra_slug': t.obra.slug, 'obra_titulo': t.obra.titulo}
                for t in temas
            ],
        })


class PersonajesPublicarAPIView(APIView):
    """Candidatos para una comparativa: personajes ya aparecidos según el progreso del usuario."""

    permission_classes = [IsAuthenticated]
    LIMITE = 30

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        progreso = ProgresoUsuario.objects.filter(usuario=request.user, obra=obra).first()
        if not progreso:
            return Response({'personajes': []})

        personajes = Personaje.objects.filter(
            unidades__obra=obra, unidades__orden_fin__lte=progreso.orden_absoluto,
        ).distinct()
        q = request.query_params.get('q', '').strip()
        if q:
            personajes = personajes.filter(nombre__icontains=q)
        personajes = personajes.order_by('nombre')[:self.LIMITE]

        return Response({
            'personajes': [{'id': p.id, 'nombre': p.nombre, 'imagen_url': p.image_url} for p in personajes],
        })


class ObraDetalleAPIView(APIView):
    """Listado completo de unidades para el árbol de progreso."""

    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        unidades = (
            UnidadNarrativa.objects.filter(obra=obra)
            .select_related('padre', 'obra')
            .order_by('orden_inicio')
        )

        return Response({
            'obra': obra_basica(obra),
            'unidades': UnidadNarrativaSerializer(unidades, many=True).data,
            'temas': temas_planos(obra),
            'obras_relacionadas': [obra_basica(o) for o in obra.obras_relacionadas()],
        })


class UnidadesBuscarAPIView(APIView):
    """Búsqueda por texto para BuscadorLocal: evita cargar obras enteras en el formulario de publicar."""

    permission_classes = [IsAuthenticated]
    LIMITE = 30

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        q = request.query_params.get('q', '').strip()

        unidades = UnidadNarrativa.objects.filter(obra=obra).select_related('padre', 'obra')
        if q:
            unidades = unidades.filter(nombre__icontains=q)
        unidades = unidades.order_by('orden_inicio')[:self.LIMITE]

        return Response({'unidades': UnidadNarrativaSerializer(unidades, many=True).data})


class ObraContextoPublicarAPIView(APIView):
    """Versión ligera para publicar: solo temas, sin unidades."""

    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        return Response({'obra': obra_basica(obra), 'temas': temas_planos(obra)})