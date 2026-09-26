from django.db.models import Max
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Obra, ProgresoUsuario, UnidadNarrativa
from ..serializers import ObraResumenSerializer, UnidadNarrativaSerializer
from .comun import contexto_suscripcion_obra, obra_basica, temas_planos


class CatalogoObrasAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        progreso_por_obra = dict(
            ProgresoUsuario.objects.filter(usuario=request.user).values_list('obra_id', 'orden_absoluto')
        )
        contexto_suscripcion = contexto_suscripcion_obra(request.user)
        ids_biblioteca = set(progreso_por_obra) | contexto_suscripcion['ids_obras_suscritas']

        todas = Obra.objects.prefetch_related('categorias').annotate(
            longitud_total=Max('unidades__orden_fin')
        )
        contexto = {'progreso_por_obra': progreso_por_obra, **contexto_suscripcion}

        return Response({
            'biblioteca': ObraResumenSerializer(
                todas.filter(id__in=ids_biblioteca), many=True, context=contexto,
            ).data,
            'descubrir': ObraResumenSerializer(
                todas.exclude(id__in=ids_biblioteca), many=True, context=contexto,
            ).data,
        })


class ObraDetalleAPIView(APIView):
    """Listado completo de unidades para el árbol de progreso."""

    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        # padre y obra precargados: sin ellos, etiqueta e imagen disparan N+1 en obras de miles de unidades.
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