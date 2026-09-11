from django.db.models import Max
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404

from subscriptions.models import Suscripcion
from .models import Obra, ProgresoUsuario, TemaTransversal, UnidadNarrativa
from .serializers import ObraResumenSerializer, UnidadNarrativaSerializer


class CatalogoObrasAPIView(APIView):
    """Separa el catálogo de obras en 'biblioteca' (progreso registrado
    o alguna suscripción) y 'descubrir' (el resto). Suscripcion.obra es
    siempre obligatorio en el modelo, incluso para suscripciones a nivel
    unidad/tema, así que basta con mirar ese campo — no hace falta
    resolver unidad__obra ni tema__obra por separado."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        progresos = ProgresoUsuario.objects.filter(usuario=user)
        progreso_por_obra = {p.obra_id: p.orden_absoluto for p in progresos}

        obras_con_suscripcion = Suscripcion.objects.filter(
            usuario=user
        ).values_list('obra_id', flat=True)

        ids_biblioteca = set(progreso_por_obra.keys()) | set(obras_con_suscripcion)

        todas = Obra.objects.prefetch_related('categorias').annotate(
            longitud_total=Max('unidades__orden_fin')
        )
        biblioteca = todas.filter(id__in=ids_biblioteca)
        descubrir = todas.exclude(id__in=ids_biblioteca)

        return Response({
            'biblioteca': ObraResumenSerializer(
                biblioteca, many=True, context={'progreso_por_obra': progreso_por_obra}
            ).data,
            'descubrir': ObraResumenSerializer(descubrir, many=True).data,
        })


class ObraDetalleAPIView(APIView):
    """Expone unidades y temas transversales de una obra, para construir
    el selector de nivel de suscripción (obra completa / unidad concreta
    / tema) en el frontend. No requiere progreso previo del usuario — a
    diferencia de ProgresoAPIView, que es progreso-céntrica."""

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