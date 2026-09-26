from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from narrative.ai_assistant import proponer_clasificacion
from narrative.models import Obra, ProgresoUsuario, ClasificacionNarrativa
from narrative.serializers import PostSerializer
from narrative.services import (
    actualizar_progreso,
    SaltoGrandeRequiereConfirmacion,
    detectar_posibles_referencias_cruzadas,
)
from narrative.services.detecciones import serializar_detecciones
from ..models import Post
from ..serializers import PostCreateSerializer
from .comun import ERROR_CRUZADA_INCOMPLETA, ERROR_TEMA_OTRA_OBRA, error_400, tema_de_otra_obra


def _asignar_frontera(post, obra, progreso, frontera_explicita):
    """Prioridad: explícita > propuesta IA > fallback al progreso actual."""
    if frontera_explicita:
        post.frontera_spoiler = frontera_explicita
        post.frontera_origen = ClasificacionNarrativa.ORIGEN_EXPLICITO
        return

    sugerencia = proponer_clasificacion(post.text, obra, progreso.unidad_actual)
    if sugerencia.es_utilizable:
        post.frontera_spoiler = sugerencia.frontera_spoiler
        post.frontera_origen = ClasificacionNarrativa.ORIGEN_IA
        post.ia_confianza = sugerencia.confianza
        post.clasificado_en = timezone.now()
    else:
        post.frontera_spoiler = progreso.unidad_actual
        post.frontera_origen = ClasificacionNarrativa.ORIGEN_FALLBACK


class PostCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, obra_slug):
        obra = get_object_or_404(Obra, slug=obra_slug)
        progreso = ProgresoUsuario.objects.filter(usuario=request.user, obra=obra).first()
        if not progreso:
            return Response(
                {'detail': 'progreso_requerido', 'obra_slug': obra.slug},
                status=status.HTTP_409_CONFLICT,
            )

        entrada = PostCreateSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data

        obra_cruzada = datos.get('obra_cruzada')
        frontera_cruzada = datos.get('frontera_cruzada')
        if bool(obra_cruzada) != bool(frontera_cruzada):
            return error_400(ERROR_CRUZADA_INCOMPLETA)

        tema = datos.get('tema')
        if tema_de_otra_obra(tema, obra.id):
            return error_400(ERROR_TEMA_OTRA_OBRA)

        if not obra_cruzada and not datos.get('descartar_referencia_cruzada'):
            detecciones = detectar_posibles_referencias_cruzadas(datos['text'], obra)
            if detecciones:
                return Response({
                    'detail': 'referencia_cruzada_detectada',
                    'detecciones': serializar_detecciones(detecciones),
                }, status=status.HTTP_409_CONFLICT)

        # El progreso solo se actualiza tras superar todas las validaciones previas.
        nuevo_progreso = datos.get('nuevo_progreso')
        if nuevo_progreso:
            try:
                progreso = actualizar_progreso(
                    request.user, obra, nuevo_progreso,
                    confirmado=datos.get('confirmar_salto_progreso', False),
                )
            except SaltoGrandeRequiereConfirmacion as exc:
                return Response({
                    'detail': str(exc),
                    'requiere_confirmacion_progreso': True,
                    'salto': exc.salto,
                }, status=status.HTTP_409_CONFLICT)
            except ValueError as exc:
                return error_400({'nuevo_progreso': [str(exc)]})

        post = Post(
            author=request.user,
            obra=obra,
            text=datos['text'],
            image=datos.get('image'),
            referencia_narrativa=datos['referencia_narrativa'],
            nivel_spoiler=datos.get('nivel_spoiler', ClasificacionNarrativa.NIVEL_MENOR),
            emocion_autor=datos.get('emocion_autor'),
            obra_cruzada=obra_cruzada,
            frontera_cruzada=frontera_cruzada,
        )
        _asignar_frontera(post, obra, progreso, datos.get('frontera_spoiler'))

        try:
            post.full_clean()
        except ValidationError as exc:
            return error_400(exc.message_dict)

        post.save()
        if tema:
            post.temas_transversales.set([tema])

        return Response(
            PostSerializer(post, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )