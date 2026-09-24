from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404

from posts.models import Post
from .models import SavedPost
from .serializers import SavedPostSerializer


class SavedPostListAPIView(APIView):
    """Lista los guardados del usuario cuyo post sigue siendo visible
    para él. Se filtra con visible_for() porque la visibilidad puede
    cambiar tras guardar (el autor sube la frontera al editar)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        saved = (
            SavedPost.objects
            .filter(user=request.user, post__in=Post.objects.visible_for(request.user))
            .select_related('post', 'post__author')
            .order_by('-created_at')
        )
        return Response(SavedPostSerializer(saved, many=True).data)


class SavedPostToggleAPIView(APIView):
    """POST guarda (idempotente vía get_or_create). DELETE elimina.
    Ambos devuelven el estado resultante en is_saved."""

    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        # Solo se pueden guardar posts visibles para el usuario.
        post = get_object_or_404(Post.objects.visible_for(request.user), id=post_id)
        SavedPost.objects.get_or_create(user=request.user, post=post)
        return Response({'is_saved': True}, status=status.HTTP_200_OK)

    def delete(self, request, post_id):
        # Sin visible_for: siempre se puede quitar un guardado propio.
        post = get_object_or_404(Post, id=post_id)
        SavedPost.objects.filter(user=request.user, post=post).delete()
        return Response({'is_saved': False}, status=status.HTTP_200_OK)