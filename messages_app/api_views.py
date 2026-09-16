from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from django.db.models import Max, Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Message
from .serializers import MessageSerializer, InboxItemSerializer


class InboxListAPIView(APIView):
    """Réplica exacta de inbox_view: misma lógica de agrupar por
    conversación, ordenar por último mensaje, calcular no leídos por
    remitente. No se reescribe con una query más "elegante" a
    propósito -- mantiene el mismo comportamiento verificado que ya
    tenía la vista Django, para no arriesgar una divergencia sutil en
    el orden o el conteo."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = (
            Message.objects
            .filter(Q(sender=request.user) | Q(receiver=request.user))
            .values('sender', 'receiver')
            .annotate(last_time=Max('created_at'))
            .order_by('-last_time')
        )

        user_ids = []
        last_message_map = {}

        for c in conversations:
            sender_id = c['sender']
            receiver_id = c['receiver']
            other_id = sender_id if sender_id != request.user.id else receiver_id

            if other_id not in user_ids:
                user_ids.append(other_id)
            last_message_map[other_id] = c['last_time']

        users = list(User.objects.filter(id__in=user_ids))
        users = sorted(users, key=lambda u: last_message_map.get(u.id), reverse=True)

        inbox_data = []
        for u in users:
            avatar = u.profile.image_url if hasattr(u, 'profile') else '/static/img/default_profile.jpg'

            last_message_obj = (
                Message.objects
                .filter(sender__in=[request.user, u], receiver__in=[request.user, u])
                .order_by('-created_at')
                .first()
            )
            last_message = last_message_obj.text if last_message_obj else ''

            unread = Message.objects.filter(
                sender=u, receiver=request.user, is_read=False
            ).count()

            inbox_data.append({
                'username': u.username,
                'avatar': avatar,
                'last_message': last_message,
                'unread_count': unread,
            })

        return Response(InboxItemSerializer(inbox_data, many=True).data)


class ChatHistoryAPIView(APIView):
    """Réplica de chat_view: marca como leídos los mensajes pendientes
    del otro usuario, envía el recuento real actualizado por WebSocket
    al propio usuario (mismo group_send que la vista Django clásica, no
    un endpoint nuevo de "marcar leído" separado), y devuelve el
    historial completo de la conversación."""

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
            .order_by('created_at')
        )

        return Response({
            'other': {'username': other.username, 'avatar': other.profile.image_url if hasattr(other, 'profile') else '/static/img/default_profile.jpg'},
            'messages': MessageSerializer(messages, many=True, context={'request': request}).data,
        })