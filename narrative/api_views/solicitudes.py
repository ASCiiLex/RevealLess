from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import SolicitudTema
from ..serializers import SolicitudTemaSerializer


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