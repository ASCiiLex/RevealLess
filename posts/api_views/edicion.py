from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comments.herencia import congelar_heredados, fronteras_de, se_rebaja
from narrative.models import ClasificacionNarrativa
from narrative.serializers import PostSerializer
from narrative.services.etiquetado import etiquetar_personajes
from ..models import Post
from ..serializers import PostUpdateSerializer
from ..videos import VideoNoValido, aplicar_video, quitar_video, resolver_video
from .comun import (
    ERROR_CRUZADA_INCOMPLETA,
    ERROR_PREVIA_CERRADA,
    ERROR_PREVIA_CERRADA_CRUZADA,
    ERROR_TEMA_OTRA_OBRA,
    ERROR_VIDEO_E_IMAGENES,
    error_400,
    error_video,
    frontera_minima,
    frontera_minima_temas,
    previa_cerrada,
    tema_de_otra_obra,
)

CAMPOS_EDITABLES = (
    'text', 'image', 'referencia_narrativa', 'nivel_spoiler',
    'emocion_autor', 'obra_cruzada', 'frontera_cruzada',
)
# Cambian qué personajes se nombran o hasta dónde se pueden etiquetar.
CAMPOS_QUE_REETIQUETAN = {'text', 'frontera_spoiler', 'referencia_narrativa', 'obra_cruzada', 'frontera_cruzada'}


def _tendra_imagen(post, datos):
    if datos.get('image'):
        return True
    if post.image and not datos.get('quitar_imagen'):
        return True
    return post.imagenes.exists()


class PostUpdateAPIView(APIView):
    """Solo el autor edita. Sin IA ni detección de referencia cruzada:
    una frontera enviada se marca ORIGEN_EXPLICITO; si no se envía, no se toca.
    En ambos casos nunca queda por debajo de su parte ni de sus temas,
    y no se puede pasar a un previo ya estrenado (los que ya lo tenían lo conservan).
    Cambiar el vídeo tampoco consulta a la IA: si revela más, la frontera la sube el autor.
    Si la frontera baja, los comentarios heredados ajenos conservan la anterior (comments/herencia.py)."""

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
        antes = fronteras_de(post)

        tema_provisto = 'tema' in datos
        tema = datos.get('tema')
        if tema_de_otra_obra(tema, post.obra_id):
            return error_400(ERROR_TEMA_OTRA_OBRA)
        if previa_cerrada(datos.get('frontera_spoiler')):
            return error_400(ERROR_PREVIA_CERRADA)
        if previa_cerrada(datos.get('frontera_cruzada')):
            return error_400(ERROR_PREVIA_CERRADA_CRUZADA)

        # Vídeo e imágenes se excluyen: se comprueba el estado resultante antes de tocar nada.
        video_url = (datos.get('video_url') or '').strip()
        tendra_video = bool(video_url) or (bool(post.video_youtube_id) and not datos.get('quitar_video'))
        if tendra_video and _tendra_imagen(post, datos):
            return error_400(ERROR_VIDEO_E_IMAGENES)
        video = None
        if video_url:
            try:
                video = resolver_video(video_url)
            except VideoNoValido as exc:
                return error_video(exc)

        for campo in CAMPOS_EDITABLES:
            if campo in datos:
                setattr(post, campo, datos[campo])
        if datos.get('quitar_imagen') and not datos.get('image'):
            post.image = None
        if video:
            aplicar_video(post, video)
        elif datos.get('quitar_video'):
            quitar_video(post)
        if 'frontera_spoiler' in datos:
            post.frontera_spoiler = datos['frontera_spoiler']
            post.frontera_origen = ClasificacionNarrativa.ORIGEN_EXPLICITO
        temas = [tema] if tema_provisto else list(post.temas_transversales.all())
        post.frontera_spoiler = frontera_minima_temas(
            frontera_minima(post.frontera_spoiler, post.referencia_narrativa), temas,
        )

        # Se valida el estado resultante: la edición puede tocar solo uno de los dos campos.
        if bool(post.obra_cruzada_id) != bool(post.frontera_cruzada_id):
            return error_400(ERROR_CRUZADA_INCOMPLETA)

        try:
            post.full_clean()
        except ValidationError as exc:
            return error_400(exc.message_dict)

        with transaction.atomic():
            post.save()
            if se_rebaja(post, antes):
                congelar_heredados(post, antes)
        if tema_provisto:
            post.temas_transversales.set([tema] if tema else [])
        if CAMPOS_QUE_REETIQUETAN & set(datos):
            etiquetar_personajes(post)

        return Response(PostSerializer(post, context={'request': request}).data)