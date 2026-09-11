from django.db.models import Max, Q
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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        solicitudes = SolicitudTema.objects.filter(usuario=request.user).select_related('obra')
        return Response(SolicitudTemaSerializer(solicitudes, many=True).data)

    def post(self, request):
        serializer = SolicitudTemaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(usuario=request.user)
        return Response(serializer.data, status=201)


class BuscarAPIView(APIView):
    """Búsqueda combinada de obras y temas transversales por texto libre.
    No incluye usuarios/hashtags/posts -- esa búsqueda ya existe en
    Django clásico (global_search.js) y queda fuera de alcance aquí,
    documentada como pendiente aparte."""

    permission_classes = [IsAuthenticated]

    MIN_CARACTERES = 2

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if len(q) < self.MIN_CARACTERES:
            return Response({'obras': [], 'temas': []})

        obras = Obra.objects.filter(titulo__icontains=q)[:10]

        temas = TemaTransversal.objects.filter(nombre__icontains=q).select_related('obra')[:10]

        return Response({
            'obras': ObraResumenSerializer(obras, many=True).data,
            'temas': [
                {
                    'id': t.id,
                    'nombre': t.nombre,
                    'obra_id': t.obra_id,
                    'obra_titulo': t.obra.titulo,
                    'obra_slug': t.obra.slug,
                }
                for t in temas
            ],
        })