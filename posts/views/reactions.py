from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from core.reacciones import totales_agrupados, totales_de
from core.serializers import serializar_reactores
from likes.models import PostReaction
from ..models import Post

CLAVES = tuple(clave for clave, _ in PostReaction.REACTION_CHOICES)


def _counts_por_reaccion(post):
    return totales_de(totales_agrupados(post.reactions.all(), 'post_id', CLAVES), post.id, CLAVES)


@login_required
@require_POST
def toggle_reaction_post(request):
    post_id = request.POST.get('post_id')
    reaction_type = request.POST.get('reaction')

    # 🔒 Validar reacción contra choices del modelo
    valid_reactions = dict(PostReaction.REACTION_CHOICES)
    if reaction_type not in valid_reactions:
        return JsonResponse({'error': 'Reacción no válida'}, status=400)

    # Solo se puede reaccionar a posts visibles para el usuario.
    post = get_object_or_404(Post.objects.visible_for(request.user), id=post_id)

    reaction, created = PostReaction.objects.get_or_create(
        user=request.user,
        post=post,
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

    # La notificación la crea PostReaction.save() (con su propia dedupe) — no duplicar aquí.

    counts = _counts_por_reaccion(post)
    total = sum(counts.values())

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "reactions",
        {
            "type": "reaction_update",
            "data": {
                "object_type": "post",
                "id": post.id,
                "count": total,
            },
        },
    )

    return JsonResponse({
        'removed': removed,
        'reaction': reaction_type,
        'counts': counts,
        'count': total,
    })


@login_required
def post_reactions_list(request, post_id):
    post = get_object_or_404(Post.objects.visible_for(request.user), id=post_id)

    return JsonResponse({
        'totals': _counts_por_reaccion(post),
        'users': serializar_reactores(request, post.reactions),
    })