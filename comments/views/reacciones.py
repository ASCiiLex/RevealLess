from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from core.serializers import serializar_reactores
from ..models import Comment, CommentReaction

REACCIONES_VALIDAS = dict(CommentReaction.REACTION_CHOICES)


def _counts_por_reaccion(comment):
    # Una sola consulta agrupada; order_by() vacío evita que el ordering del modelo rompa el GROUP BY.
    counts = dict.fromkeys(REACCIONES_VALIDAS, 0)
    filas = comment.reactions.order_by().values('reaction').annotate(n=Count('id'))
    for fila in filas:
        if fila['reaction'] in counts:
            counts[fila['reaction']] = fila['n']
    return counts


def _emitir_actualizacion(comment_id, total):
    async_to_sync(get_channel_layer().group_send)(
        'reactions',
        {
            'type': 'reaction_update',
            'data': {'object_type': 'comment', 'id': comment_id, 'count': total},
        },
    )


@login_required
@require_POST
def toggle_reaction_comment(request, comment_id):
    reaction_type = request.POST.get('reaction')
    if reaction_type not in REACCIONES_VALIDAS:
        return JsonResponse({'error': 'Reacción no válida'}, status=400)

    comment = get_object_or_404(Comment.objects.visible_for(request.user), id=comment_id)

    reaction, created = CommentReaction.objects.get_or_create(
        user=request.user, comment=comment, defaults={'reaction': reaction_type}
    )

    removed = False
    if not created:
        if reaction.reaction == reaction_type:
            reaction.delete()
            removed = True
        else:
            reaction.reaction = reaction_type
            reaction.save()

    # La notificación la crea CommentReaction.save() — no duplicar aquí.

    counts = _counts_por_reaccion(comment)
    total = sum(counts.values())
    _emitir_actualizacion(comment.id, total)

    return JsonResponse({
        'removed': removed,
        'reaction': reaction_type,
        'counts': counts,
        'count': total,
    })


@login_required
def comment_reactions_list(request, comment_id):
    comment = get_object_or_404(Comment.objects.visible_for(request.user), id=comment_id)

    return JsonResponse({
        'totals': _counts_por_reaccion(comment),
        'users': serializar_reactores(request, comment.reactions),
    })