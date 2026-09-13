from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404

from narrative.models import Obra, ProgresoUsuario, ClasificacionNarrativa
from narrative.services import actualizar_progreso, SaltoGrandeRequiereConfirmacion
from narrative.ai_assistant import proponer_clasificacion
from narrative.serializers import PostSerializer
from .models import Post
from .serializers import PostCreateSerializer


class PostCreateAPIView(APIView):
    """Réplica exacta de create_post (posts/views/create.py): exige
    progreso previo en la obra (404 con detalle si no existe, en vez de
    redirect -- el frontend decide qué hacer, ej. mostrar el paso de
    declarar progreso), permite actualizar el progreso desde el propio
    formulario, usa la IA para sugerir frontera si no se especifica
    explícitamente, cae al fallback (progreso actual) si la IA no es
    utilizable. Misma secuencia de pasos que la vista Django, sin
    reordenar ni simplificar la lógica de negocio."""

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

        post = Post(
            author=request.user,
            obra=obra,
            text=datos['text'],
            image=datos.get('image'),
            referencia_narrativa=datos['referencia_narrativa'],
            nivel_spoiler=datos.get('nivel_spoiler', 'menor'),
        )

        if datos.get('frontera_spoiler'):
            post.frontera_spoiler = datos['frontera_spoiler']
            post.frontera_origen = ClasificacionNarrativa.ORIGEN_EXPLICITO
        else:
            sugerencia = proponer_clasificacion(post.text, obra, progreso.unidad_actual)
            if sugerencia.es_utilizable:
                post.frontera_spoiler = sugerencia.frontera_spoiler
                post.frontera_origen = ClasificacionNarrativa.ORIGEN_IA
                post.ia_confianza = sugerencia.confianza
                post.clasificado_en = timezone.now()
            else:
                post.frontera_spoiler = progreso.unidad_actual
                post.frontera_origen = ClasificacionNarrativa.ORIGEN_FALLBACK

        try:
            post.full_clean()
        except ValidationError as exc:
            return Response({'detail': exc.message_dict}, status=status.HTTP_400_BAD_REQUEST)

        post.save()
        return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)