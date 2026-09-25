from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User

from .models import Message, MessageReaction


@login_required
def inbox_react_view(request):
    """Monta React para la bandeja de mensajes."""
    return render(request, 'messages/inbox_react.html')


@login_required
def chat_react_view(request, username):
    """Monta React para el chat. Los WebSockets /ws/chat/<username>/ y
    /ws/messages/ (registrados en core/routing.py) funcionan igual, sin
    cambios de infraestructura -- mismo origen que la página HTML clásica."""
    if username == request.user.username:
        return redirect('inbox')
    get_object_or_404(User, username=username)
    return render(request, 'messages/chat_react.html', {'username': username})


def _counts_por_reaccion(message):
    return {
        clave: message.reactions.filter(reaction=clave).count()
        for clave, _ in MessageReaction.REACTION_CHOICES
    }


@login_required
@require_POST
def toggle_reaction_message(request, message_id):
    reaction_type = request.POST.get('reaction')

    valid_reactions = dict(MessageReaction.REACTION_CHOICES)
    if reaction_type not in valid_reactions:
        return JsonResponse({'error': 'Reacción no válida'}, status=400)

    message = get_object_or_404(Message, id=message_id)

    # Solo remitente o destinatario del mensaje pueden reaccionar --
    # reaccionar a un mensaje de una conversación ajena no tiene sentido.
    if request.user not in (message.sender, message.receiver):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    reaction, created = MessageReaction.objects.get_or_create(
        user=request.user,
        message=message,
        defaults={'reaction': reaction_type}
    )

    removed = False

    if not created:
        if reaction.reaction == reaction_type:
            reaction.delete()
            removed = True
        else:
            reaction.reaction = reaction_type
            reaction.save()

    counts = _counts_por_reaccion(message)
    total = sum(counts.values())

    return JsonResponse({
        'removed': removed,
        'reaction': reaction_type,
        'counts': counts,
        'count': total,
    })


@login_required
def message_reactions_list(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    if request.user not in (message.sender, message.receiver):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    totals = _counts_por_reaccion(message)

    return JsonResponse({'totals': totals})