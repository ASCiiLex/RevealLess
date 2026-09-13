from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Follow
from .serializers import FollowToggleSerializer


class FollowToggleAPIView(APIView):
    """POST crea el follow (idempotente vía get_or_create, dispara la
    notificación existente solo si se crea de verdad). DELETE lo
    elimina. No se junta en un único endpoint PATCH porque, a
    diferencia de Suscripcion, Follow no tiene un estado 'activo' que
    alternar -- solo existe o no existe."""

    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        if request.user.username == username:
            return Response(
                {'detail': 'No puedes seguirte a ti mismo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        followed = get_object_or_404(User, username=username)
        Follow.objects.get_or_create(follower=request.user, followed=followed)
        return Response(FollowToggleSerializer({'is_following': True}).data)

    def delete(self, request, username):
        followed = get_object_or_404(User, username=username)
        Follow.objects.filter(follower=request.user, followed=followed).delete()
        return Response(FollowToggleSerializer({'is_following': False}).data)