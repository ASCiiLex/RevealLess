from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404

from comments.models import CommentReaction
from comments.serializers import CommentSerializer
from likes.models import PostReaction
from narrative.models import Obra, ProgresoUsuario, ClasificacionNarrativa
from narrative.services import actualizar_progreso, SaltoGrandeRequiereConfirmacion
from narrative.ai_assistant import proponer_clasificacion
from narrative.serializers import PostSerializer
from .models import Post
from .serializers import PostCreateSerializer, PostUpdateSerializer
from .views.post_detail import get_sorted_comments


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
            emocion_autor=datos.get('emocion_autor'),
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
        return Response(PostSerializer(post, context={'request': request}).data, status=status.HTTP_201_CREATED)


class PostUpdateAPIView(APIView):
    """Edita un post ya publicado. Solo el autor puede editarlo (403 si
    no). No vuelve a consultar progreso ni dispara la IA -- si se envía
    frontera_spoiler, se marca ORIGEN_EXPLICITO (edición manual
    consciente); si no se envía, la frontera actual no se toca."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        if post.author != request.user:
            return Response(
                {'detail': 'No puedes editar publicaciones de otro usuario.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        entrada = PostUpdateSerializer(data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data

        if 'text' in datos:
            post.text = datos['text']
        if 'image' in datos:
            post.image = datos['image']
        if 'referencia_narrativa' in datos:
            post.referencia_narrativa = datos['referencia_narrativa']
        if 'nivel_spoiler' in datos:
            post.nivel_spoiler = datos['nivel_spoiler']
        if 'emocion_autor' in datos:
            post.emocion_autor = datos['emocion_autor']
        if 'frontera_spoiler' in datos:
            post.frontera_spoiler = datos['frontera_spoiler']
            post.frontera_origen = ClasificacionNarrativa.ORIGEN_EXPLICITO

        try:
            post.full_clean()
        except ValidationError as exc:
            return Response({'detail': exc.message_dict}, status=status.HTTP_400_BAD_REQUEST)

        post.save()
        return Response(PostSerializer(post, context={'request': request}).data)


class PostDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, post_id):
        post = get_object_or_404(Post.objects.visible_for(request.user), id=post_id)
        sort = request.query_params.get('sort', 'recent')

        comments = get_sorted_comments(request.user, post, sort)

        reaction_map = {}
        post_reaction = None
        if request.user.is_authenticated:
            reaction_map = dict(
                CommentReaction.objects.filter(
                    user=request.user, comment__post=post
                ).values_list('comment_id', 'reaction')
            )
            pr = PostReaction.objects.filter(user=request.user, post=post).first()
            post_reaction = pr.reaction if pr else None

        return Response({
            'post': PostSerializer(post, context={'request': request}).data,
            'post_reaction': post_reaction,
            'comments': CommentSerializer(comments, many=True, context={'reaction_map': reaction_map}).data,
        })