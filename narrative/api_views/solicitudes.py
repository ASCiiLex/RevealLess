from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import SolicitudObra, SolicitudTema
from ..serializers import SolicitudObraSerializer, SolicitudTemaSerializer
from ..services.solicitudes_obra import SolicitudNoValida, proponer_obra


class SolicitudTemaListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        solicitudes = SolicitudTema.objects.filter(usuario=request.user).select_related('obra')
        return Response(SolicitudTemaSerializer(solicitudes, many=True).data)

    def post(self, request):
        serializer = SolicitudTemaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(usuario=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# Freno al spam de sugerencias, además del tope de pendientes por usuario.
@method_decorator(ratelimit(key='user', rate='10/h', method='POST', block=True), name='post')
class SolicitudObraListCreateAPIView(APIView):
    """Sugerencias de obras del propio usuario. Crear solo deja la solicitud: la obra se crea al aprobarla."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        solicitudes = SolicitudObra.objects.filter(usuario=request.user).select_related('obra')
        return Response(SolicitudObraSerializer(solicitudes, many=True).data)

    def post(self, request):
        entrada = SolicitudObraSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            solicitud = proponer_obra(request.user, **entrada.validated_data)
        except SolicitudNoValida as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SolicitudObraSerializer(solicitud).data, status=status.HTTP_201_CREATED)