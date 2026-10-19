from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from narrative.models import ClasificacionNarrativa
from narrative.services.fronteras import previa_cerrada
from ..models import Comment
from ..serializers import CommentUpdateSerializer
from .crear import MENSAJE_PREVIA_CERRADA
from .fronteras import ajustar_frontera
from .respuestas import datos_clasificacion

CAMPOS_EDITABLES = ('text', 'emocion_autor', 'referencia_narrativa', 'obra_cruzada', 'frontera_cruzada')


class CommentUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, comment_id):
        comment = get_object_or_404(Comment.objects.select_related('post'), id=comment_id)

        if comment.user != request.user:
            return Response(
                {'detail': 'No puedes editar comentarios de otro usuario.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        entrada = CommentUpdateSerializer(data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data

        # Solo se comprueba lo que cambia: un comentario que ya tenía ese previo lo conserva.
        if previa_cerrada(datos.get('frontera_spoiler')) or previa_cerrada(datos.get('frontera_cruzada')):
            return Response({'detail': MENSAJE_PREVIA_CERRADA}, status=status.HTTP_400_BAD_REQUEST)

        for campo in CAMPOS_EDITABLES:
            if campo in datos:
                setattr(comment, campo, datos[campo])
        if 'frontera_spoiler' in datos:
            comment.frontera_spoiler = datos['frontera_spoiler']
            comment.frontera_origen = ClasificacionNarrativa.ORIGEN_EXPLICITO
        ajustar_frontera(comment)

        # Se valida el estado resultante: la edición puede tocar solo uno de los dos campos.
        if bool(comment.obra_cruzada_id) != bool(comment.frontera_cruzada_id):
            return Response(
                {'detail': 'Indica la obra cruzada y su frontera juntas, o ninguna de las dos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            comment.full_clean()
        except ValidationError as exc:
            return Response({'detail': exc.message_dict}, status=status.HTTP_400_BAD_REQUEST)

        comment.save()
        return Response({
            'id': comment.id,
            'text': comment.text,
            **datos_clasificacion(comment),
        })


@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.user != request.user:
        return JsonResponse({'error': 'No autorizado'}, status=403)

    comment.delete()
    return JsonResponse({'success': True})