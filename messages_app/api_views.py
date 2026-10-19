from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from django.db.models import Case, Count, F, IntegerField, Q, When
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Message
from .serializers import MessageSerializer, InboxItemSerializer

AVATAR_POR_DEFECTO = '/static/img/default_profile.jpg'


class InboxListAPIView(APIView):
    """Conversaciones del usuario ordenadas por su último mensaje, con ese mensaje y los no leídos
    de cada remitente. Número fijo de consultas, tenga las conversaciones que tenga."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        yo = request.user

        # Último mensaje de cada conversación en una sola consulta (DISTINCT ON de Postgres).
        ultimos = list(
            Message.objects
            .filter(Q(sender=yo) | Q(receiver=yo))
            .annotate(otro=Case(
                When(sender=yo, then=F('receiver')), default=F('sender'), output_field=IntegerField(),
            ))
            .order_by('otro', '-created_at')
            .distinct('otro')
            .values('otro', 'text', 'created_at')
        )
        ultimos.sort(key=lambda m: m['created_at'], reverse=True)

        no_leidos = dict(
            Message.objects.filter(receiver=yo, is_read=False)
            .order_by().values('sender').annotate(n=Count('id')).values_list('sender', 'n')
        )
        usuarios = User.objects.select_related('profile').in_bulk([m['otro'] for m in ultimos])

        inbox_data = []
        for mensaje in ultimos:
            otro = usuarios.get(mensaje['otro'])
            if otro is None:
                continue
            inbox_data.append({
                'username': otro.username,
                'avatar': otro.profile.image_url if hasattr(otro, 'profile') else AVATAR_POR_DEFECTO,
                'last_message': mensaje['text'],
                'unread_count': no_leidos.get(otro.id, 0),
            })

        return Response(InboxItemSerializer(inbox_data, many=True).data)


class ChatHistoryAPIView(APIView):
    """Réplica de chat_view: marca como leídos los mensajes pendientes
    del otro usuario, envía el recuento real actualizado por WebSocket
    al propio usuario (mismo group_send que la vista Django clásica, no
    un endpoint nuevo de "marcar leído" separado), y devuelve el
    historial completo de la conversación con la reacción de cada mensaje."""

    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        if username == request.user.username:
            return Response({'detail': 'No puedes chatear contigo mismo.'}, status=400)

        other = get_object_or_404(User, username=username)

        Message.objects.filter(sender=other, receiver=request.user, is_read=False).update(is_read=True)

        unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'messages_{request.user.id}',
            {'type': 'new_message_alert', 'count': unread_count},
        )

        messages = (
            Message.objects
            .filter(sender__in=[request.user, other], receiver__in=[request.user, other])
            .select_related('sender', 'receiver')
            .prefetch_related('reactions')
            .order_by('created_at')
        )

        return Response({
            'other': {
                'username': other.username,
                'avatar': other.profile.image_url if hasattr(other, 'profile') else AVATAR_POR_DEFECTO,
            },
            'messages': MessageSerializer(messages, many=True).data,
        })