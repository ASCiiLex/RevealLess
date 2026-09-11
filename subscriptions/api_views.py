from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Suscripcion
from .serializers import SuscripcionSerializer, SuscripcionCreateSerializer
from .services import crear_suscripcion, eliminar_suscripcion


class SuscripcionListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        suscripciones = Suscripcion.objects.filter(usuario=request.user).select_related(
            'obra', 'unidad', 'tema'
        )
        return Response(SuscripcionSerializer(suscripciones, many=True).data)

    def post(self, request):
        entrada = SuscripcionCreateSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        try:
            suscripcion = crear_suscripcion(
                usuario=request.user,
                obra=entrada.validated_data['obra'],
                unidad=entrada.validated_data.get('unidad'),
                tema=entrada.validated_data.get('tema'),
            )
        except (ValueError, DjangoValidationError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            SuscripcionSerializer(suscripcion).data, status=status.HTTP_201_CREATED
        )


class SuscripcionDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        suscripcion = Suscripcion.objects.filter(pk=pk, usuario=request.user).first()
        if not suscripcion:
            return Response(status=status.HTTP_404_NOT_FOUND)

        eliminar_suscripcion(
            usuario=request.user,
            obra=suscripcion.obra,
            unidad=suscripcion.unidad,
            tema=suscripcion.tema,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)