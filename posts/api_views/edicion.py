from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from narrative.models import ClasificacionNarrativa
from narrative.serializers import PostSerializer
from ..models import Post
from ..serializers import PostUpdateSerializer
from .comun import ERROR_CRUZADA_INCOMPLETA, ERROR_TEMA_OTRA_OBRA, error_400, tema_de_otra_obra

CAMPOS_EDITABLES = (
    'text', 'image', 'referencia_narrativa', 'nivel_spoiler',
    'emocion_autor', 'obra_cruzada', 'frontera_cruzada',
)


class PostUpdateAPIView(APIView):
    """Solo el autor edita. Sin IA ni detección de referencia cruzada:
    una frontera enviada se marca ORIGEN_EXPLICITO; si no se envía, no se toca."""

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

        tema_provisto = 'tema' in datos
        tema = datos.get('tema')
        if tema_de_otra_obra(tema, post.obra_id):
            return error_400(ERROR_TEMA_OTRA_OBRA)

        for campo in CAMPOS_EDITABLES:
            if campo in datos:
                setattr(post, campo, datos[campo])
        if 'frontera_spoiler' in datos:
            post.frontera_spoiler = datos['frontera_spoiler']
            post.frontera_origen = ClasificacionNarrativa.ORIGEN_EXPLICITO

        # Se valida el estado resultante: la edición puede tocar solo uno de los dos campos.
        if bool(post.obra_cruzada_id) != bool(post.frontera_cruzada_id):
            return error_400(ERROR_CRUZADA_INCOMPLETA)

        try:
            post.full_clean()
        except ValidationError as exc:
            return error_400(exc.message_dict)

        post.save()
        if tema_provisto:
            post.temas_transversales.set([tema] if tema else [])

        return Response(PostSerializer(post, context={'request': request}).data)