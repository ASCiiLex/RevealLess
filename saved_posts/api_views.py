from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404

from posts.models import Post
from .models import SavedPost
from .serializers import SavedPostSerializer


class SavedPostListAPIView(APIView):
    """Réplica de saved_posts_view: lista los posts guardados del
    usuario autenticado. No aplica visible_for() explícitamente porque
    un post guardado que el usuario ya vio y guardó es, por definición,
    algo que ya le era visible en su momento -- a diferencia del feed o
    la búsqueda, donde el contenido puede pertenecer a otro usuario que
    nunca lo vio antes."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        saved = SavedPost.objects.filter(user=request.user).select_related(
            'post', 'post__author'
        ).order_by('-created_at')
        return Response(SavedPostSerializer(saved, many=True).data)


class SavedPostToggleAPIView(APIView):
    """POST guarda (idempotente vía get_or_create). DELETE elimina."""

    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        # Solo se pueden guardar posts visibles para el usuario.
        post = get_object_or_404(Post.objects.visible_for(request.user), id=post_id)
        SavedPost.objects.get_or_create(user=request.user, post=post)
        return Response(status=status.HTTP_200_OK)

    def delete(self, request, post_id):
        # Sin visible_for: siempre se puede quitar un guardado propio.
        post = get_object_or_404(Post, id=post_id)
        SavedPost.objects.filter(user=request.user, post=post).delete()
        return Response(status=status.HTTP_200_OK)