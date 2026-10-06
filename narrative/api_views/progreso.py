from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Obra, ProgresoUsuario, UnidadNarrativa
from ..serializers import ProgresoUsuarioSerializer, UnidadNarrativaSerializer
from ..services import actualizar_progreso, asegurar_unidad_previa, SaltoGrandeRequiereConfirmacion
from .comun import entero_o_none, es_verdadero, obra_basica


class ProgresoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        # Obra por estrenar: sin esta unidad no habría dónde declarar progreso.
        asegurar_unidad_previa(obra)
        unidades = (
            UnidadNarrativa.objects.filter(obra=obra)
            .select_related('padre', 'obra')
            .order_by('orden_inicio')
        )
        progreso = (
            ProgresoUsuario.objects.filter(usuario=request.user, obra=obra)
            .select_related('unidad_actual__padre', 'unidad_actual__obra')
            .first()
        )

        datos_obra = obra_basica(obra)
        return Response({
            'obra': {'titulo': datos_obra['titulo'], 'slug': datos_obra['slug']},
            'unidades': UnidadNarrativaSerializer(unidades, many=True).data,
            'progreso': ProgresoUsuarioSerializer(progreso).data if progreso else None,
        })

    def post(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        unidad = get_object_or_404(
            UnidadNarrativa,
            id=entero_o_none(request.data.get('unidad_actual'), 'unidad_actual'),
            obra=obra,
        )

        try:
            # Gestión explícita de progreso: se puede retroceder para corregir, siempre confirmando.
            progreso = actualizar_progreso(
                request.user, obra, unidad,
                confirmado=es_verdadero(request.data.get('confirmado', False)),
                permitir_retroceso=True,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except SaltoGrandeRequiereConfirmacion as exc:
            return Response({
                'detail': str(exc),
                'requiere_confirmacion': True,
                'salto': exc.salto,
            }, status=status.HTTP_409_CONFLICT)

        return Response(ProgresoUsuarioSerializer(progreso).data)


class ProgresoExisteAPIView(APIView):
    """Solo confirma si hay progreso declarado, sin serializar unidades (clave en obras grandes)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        existe = ProgresoUsuario.objects.filter(usuario=request.user, obra=obra).exists()
        return Response({'existe': existe})