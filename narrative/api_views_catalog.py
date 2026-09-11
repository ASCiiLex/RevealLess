from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from subscriptions.models import Suscripcion
from .models import Obra, ProgresoUsuario
from .serializers import ObraResumenSerializer


class CatalogoObrasAPIView(APIView):
    """Separa el catálogo de obras en 'biblioteca' (progreso registrado
    o alguna suscripción) y 'descubrir' (el resto). Suscripcion.obra es
    siempre obligatorio en el modelo, incluso para suscripciones a nivel
    unidad/tema, así que basta con mirar ese campo — no hace falta
    resolver unidad__obra ni tema__obra por separado."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        obras_con_progreso = ProgresoUsuario.objects.filter(
            usuario=user
        ).values_list('obra_id', flat=True)
        obras_con_suscripcion = Suscripcion.objects.filter(
            usuario=user
        ).values_list('obra_id', flat=True)

        ids_biblioteca = set(obras_con_progreso) | set(obras_con_suscripcion)

        todas = Obra.objects.prefetch_related('categorias')
        biblioteca = todas.filter(id__in=ids_biblioteca)
        descubrir = todas.exclude(id__in=ids_biblioteca)

        return Response({
            'biblioteca': ObraResumenSerializer(biblioteca, many=True).data,
            'descubrir': ObraResumenSerializer(descubrir, many=True).data,
        })