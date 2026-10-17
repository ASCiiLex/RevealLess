from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Message, MessageReaction
from .salas import sala_chat


@login_required
def inbox_react_view(request):
    """Monta React para la bandeja de mensajes."""
    return render(request, 'messages/inbox_react.html')


@login_required
def chat_react_view(request, username):
    """Monta React para el chat; el tiempo real va por /ws/chat/<username>/ y /ws/messages/ (core/routing.py)."""
    if username == request.user.username:
        return redirect('inbox')
    get_object_or_404(User, username=username)
    return render(request, 'messages/chat_react.html', {'username': username})


@login_required
@require_POST
def toggle_reaction_message(request, message_id):
    """Solo reacciona quien recibe el mensaje, con una reacción como máximo; repetir la misma la quita.
    El cambio se reenvía a la sala del chat para que los dos lo vean al momento."""
    reaction_type = request.POST.get('reaction')
    if reaction_type not in dict(MessageReaction.REACTION_CHOICES):
        return JsonResponse({'error': 'Reacción no válida'}, status=400)

    message = get_object_or_404(Message.objects.select_related('sender', 'receiver'), id=message_id)
    if request.user != message.receiver:
        return JsonResponse({'error': 'Solo quien recibe el mensaje puede reaccionar'}, status=403)

    actual = MessageReaction.objects.filter(user=request.user, message=message).first()
    if actual and actual.reaction == reaction_type:
        actual.delete()
        reaccion = None
    else:
        MessageReaction.objects.update_or_create(
            user=request.user, message=message, defaults={'reaction': reaction_type},
        )
        reaccion = reaction_type

    async_to_sync(get_channel_layer().group_send)(
        sala_chat(message.sender.username, message.receiver.username),
        {'type': 'reaction_message', 'data': {'message_id': message.id, 'reaccion': reaccion}},
    )
    return JsonResponse({'reaccion': reaccion})