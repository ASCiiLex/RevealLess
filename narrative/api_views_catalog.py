from django.db.models import Max
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404

from subscriptions.models import Suscripcion
from .models import Obra, ProgresoUsuario, TemaTransversal, UnidadNarrativa, SolicitudTema
from .serializers import ObraResumenSerializer, UnidadNarrativaSerializer, SolicitudTemaSerializer


class CatalogoObrasAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        progresos = ProgresoUsuario.objects.filter(usuario=user)
        progreso_por_obra = {p.obra_id: p.orden_absoluto for p in progresos}

        ids_obras_suscritas = set(
            Suscripcion.objects.filter(usuario=user).values_list('obra_id', flat=True)
        )

        ids_biblioteca = set(progreso_por_obra.keys()) | ids_obras_suscritas

        todas = Obra.objects.prefetch_related('categorias').annotate(
            longitud_total=Max('unidades__orden_fin')
        )
        biblioteca = todas.filter(id__in=ids_biblioteca)
        descubrir = todas.exclude(id__in=ids_biblioteca)

        contexto = {
            'progreso_por_obra': progreso_por_obra,
            'ids_obras_suscritas': ids_obras_suscritas,
        }

        return Response({
            'biblioteca': ObraResumenSerializer(biblioteca, many=True, context=contexto).data,
            'descubrir': ObraResumenSerializer(descubrir, many=True, context=contexto).data,
        })


class ObraDetalleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        unidades = UnidadNarrativa.objects.filter(obra=obra).order_by('orden_inicio')
        temas = TemaTransversal.objects.filter(obra=obra).order_by('nombre')

        return Response({
            'obra': {'id': obra.id, 'titulo': obra.titulo, 'slug': obra.slug},
            'unidades': UnidadNarrativaSerializer(unidades, many=True).data,
            'temas': [{'id': t.id, 'nombre': t.nombre} for t in temas],
        })


class SolicitudTemaListCreateAPIView(APIView):
    """GET lista las solicitudes del propio usuario (cualquier estado).
    POST crea una nueva, siempre en estado pendiente -- nunca crea el
    TemaTransversal directamente, eso solo ocurre vía la acción de admin
    'Aprobar solicitudes'."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        solicitudes = SolicitudTema.objects.filter(usuario=request.user).select_related('obra')
        return Response(SolicitudTemaSerializer(solicitudes, many=True).data)

    def post(self, request):
        serializer = SolicitudTemaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(usuario=request.user)
        return Response(serializer.data, status=201)