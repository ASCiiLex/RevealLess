from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from messages_app.models import Message
from notifications.models import Notification


class MeAPIView(APIView):
    """Datos mínimos que necesita el header de React: identidad del
    usuario y un único contador de no-leídos (notificaciones + mensajes
    sin leer). No sustituye a notifications_view ni a inbox_view, que
    siguen siendo las vistas HTML completas."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        avatar_url = (
            user.profile.image_url
            if hasattr(user, 'profile')
            else '/static/img/default_profile.jpg'
        )
        unread_notifications = Notification.objects.filter(user=user, seen=False).count()
        unread_messages = Message.objects.filter(receiver=user, is_read=False).count()

        return Response({
            'username': user.username,
            'avatar_url': avatar_url,
            'unread_count': unread_notifications + unread_messages,
        })