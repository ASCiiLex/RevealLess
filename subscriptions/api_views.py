from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from narrative.services.personajes import progreso_por_obra
from .models import Suscripcion
from .serializers import SuscripcionSerializer, SuscripcionCreateSerializer
from .services import crear_suscripcion, eliminar_suscripcion, silenciar_suscripcion, reactivar_suscripcion


def _contexto(request):
    # El personaje se presenta con la etapa que el usuario ya ha superado.
    return {'progreso_por_obra': progreso_por_obra(request.user)}


class SuscripcionListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        suscripciones = (
            Suscripcion.objects.filter(usuario=request.user)
            .select_related('obra', 'unidad', 'tema', 'personaje')
            .prefetch_related('personaje__etapas__visible_tras')
        )
        return Response(SuscripcionSerializer(suscripciones, many=True, context=_contexto(request)).data)

    def post(self, request):
        entrada = SuscripcionCreateSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        try:
            suscripcion = crear_suscripcion(
                usuario=request.user,
                obra=entrada.validated_data.get('obra'),
                unidad=entrada.validated_data.get('unidad'),
                tema=entrada.validated_data.get('tema'),
                personaje=entrada.validated_data.get('personaje'),
            )
        except (ValueError, DjangoValidationError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            SuscripcionSerializer(suscripcion, context=_contexto(request)).data,
            status=status.HTTP_201_CREATED,
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
            personaje=suscripcion.personaje,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


def _parsear_booleano(valor):
    """Interpreta 'activa' de forma robusta sea cual sea el formato de
    entrada: JSON manda True/False nativos, pero multipart/form-encoded
    (incluido el cliente de test de DRF por defecto) serializa todo como
    texto -- 'False' como string es verdadero en Python si no se
    normaliza antes de evaluarlo."""
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in ('true', '1', 'yes')
    return bool(valor)


class SuscripcionToggleActivaAPIView(APIView):
    """PATCH activa/silencia una suscripción existente. Separado de
    SuscripcionDeleteAPIView porque son acciones semánticamente distintas
    (silenciar no borra nada, solo excluye del feed) y de
    SuscripcionListCreateAPIView porque no es una creación."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        suscripcion = Suscripcion.objects.filter(pk=pk, usuario=request.user).first()
        if not suscripcion:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if 'activa' not in request.data:
            return Response(
                {'detail': "Falta el campo 'activa' (true o false)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        activa = _parsear_booleano(request.data.get('activa'))

        if activa:
            reactivar_suscripcion(suscripcion)
        else:
            silenciar_suscripcion(suscripcion)

        suscripcion.refresh_from_db()
        return Response(SuscripcionSerializer(suscripcion, context=_contexto(request)).data)