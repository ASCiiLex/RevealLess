from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Max
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Message


@login_required
def inbox_view(request):

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
        last_time = c['last_time']

        other_id = sender_id if sender_id != request.user.id else receiver_id

        if other_id not in user_ids:
            user_ids.append(other_id)

        last_message_map[other_id] = last_time

    users = list(User.objects.filter(id__in=user_ids))

    users = sorted(
        users,
        key=lambda u: last_message_map.get(u.id),
        reverse=True
    )

    inbox_users = []

    for u in users:

        avatar = (
            u.profile.image_url
            if hasattr(u, "profile")
            else "/static/img/default_profile.jpg"
        )

        last_message_obj = (
            Message.objects
            .filter(
                sender__in=[request.user, u],
                receiver__in=[request.user, u]
            )
            .order_by('-created_at')
            .first()
        )

        last_message = last_message_obj.text if last_message_obj else ""

        unread = Message.objects.filter(
            sender=u,
            receiver=request.user,
            is_read=False
        ).count()

        inbox_users.append({
            "username": u.username,
            "avatar": avatar,
            "last_message": last_message,
            "unread_count": unread,
        })

    return render(request, 'messages/inbox.html', {
        'users': inbox_users,
    })


@login_required
def chat_view(request, username):

    if username == request.user.username:
        return redirect('inbox')

    other = get_object_or_404(User, username=username)

    # marcar como leídos
    Message.objects.filter(
        sender=other,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    # 🔥 recalcular contador real tras marcar como leídos
    unread_count = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    # 🔥 enviar contador REAL (no reset ciego)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"messages_{request.user.id}",
        {
            "type": "new_message_alert",
            "count": unread_count
        }
    )

    messages = (
        Message.objects
        .filter(
            sender__in=[request.user, other],
            receiver__in=[request.user, other]
        )
        .select_related('sender', 'receiver')
        .order_by('created_at')
    )

    return render(request, 'messages/chat.html', {
        'other': other,
        'messages': messages,
    })


@login_required
def inbox_react_view(request):
    """Vista mínima que monta el punto de entrada de React para la
    bandeja de mensajes (Fase 4). No reemplaza inbox_view."""
    return render(request, 'messages/inbox_react.html')


@login_required
def chat_react_view(request, username):
    """Vista mínima que monta el punto de entrada de React para el
    chat (Fase 4). No reemplaza chat_view. El WebSocket de
    /ws/chat/<username>/ y /ws/messages/ (ya registrados en
    core/routing.py) funcionan igual desde esta página, sin cambios de
    infraestructura -- mismo origen que la página HTML clásica."""
    if username == request.user.username:
        return redirect('inbox_react')
    get_object_or_404(User, username=username)
    return render(request, 'messages/chat_react.html', {'username': username})