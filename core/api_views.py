from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from messages_app.models import Message
from notifications.models import Notification


class MeAPIView(APIView):
    """Datos mínimos que necesita el header de React: identidad del
    usuario y contadores de no-leídos. unread_notifications y
    unread_messages son fuentes independientes sin solape -- no existe
    hoy ninguna Notification de tipo 'message' generándose realmente
    (el choice existe en el modelo pero nadie lo dispara), así que
    sumarlos en unread_count no duplica nada."""

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
            'unread_notifications': unread_notifications,
            'unread_messages': unread_messages,
            'unread_count': unread_notifications + unread_messages,
        })