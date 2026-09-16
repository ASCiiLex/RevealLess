from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from narrative.models import ClasificacionNarrativa
from posts.models import Post
from .models import Comment, CommentReaction
from notifications.models import Notification


EMOCION_VALIDAS = dict(ClasificacionNarrativa.EMOCION_CHOICES)


def _counts_por_reaccion(comment):
    return {
        clave: comment.reactions.filter(reaction=clave).count()
        for clave, _ in CommentReaction.REACTION_CHOICES
    }


@login_required
@require_POST
def add_comment(request):
    post_id = request.POST.get("post_id")
    text = request.POST.get("text", "").strip()
    parent_id = request.POST.get("parent_id")
    emocion_autor = request.POST.get("emocion_autor") or None

    if not text:
        return JsonResponse({"error": "Texto vacío"}, status=400)

    if emocion_autor and emocion_autor not in EMOCION_VALIDAS:
        return JsonResponse({"error": "Emoción no válida"}, status=400)

    post = get_object_or_404(Post, id=post_id)

    parent = None
    if parent_id:
        parent = get_object_or_404(Comment, id=parent_id, post=post)

    comment = Comment.objects.create(
        user=request.user, post=post, parent=parent, text=text,
        # referencia_narrativa es obligatorio (ClasificacionNarrativa):
        # un comentario hereda el contexto narrativo del post al que
        # responde, coherente con frontera_origen=ORIGEN_HEREDADO_POST
        # (default del modelo, que ya asume esta herencia).
        referencia_narrativa=post.referencia_narrativa,
        emocion_autor=emocion_autor,
    )

    if parent is None and post.author != request.user:
        Notification.objects.create(
            actor=request.user,
            user=post.author,
            verb="comentó tu post",
            target_type="post",
            target_id=post.id,
        )

    if parent and parent.user != request.user:
        Notification.objects.create(
            actor=request.user,
            user=parent.user,
            verb="respondió a tu comentario",
            target_type="post",
            target_id=post.id,
        )

    return JsonResponse(
        {
            "id": comment.id,
            "user": comment.user.username,
            "text": comment.text,
            "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
            "parent_id": comment.parent.id if comment.parent else None,
            "emocion_autor": comment.emocion_autor,
            "likes_count": 0,
        }
    )


@login_required
@require_POST
def toggle_reaction_comment(request, comment_id):
    reaction_type = request.POST.get("reaction")

    valid_reactions = dict(CommentReaction.REACTION_CHOICES)
    if reaction_type not in valid_reactions:
        return JsonResponse({"error": "Reacción no válida"}, status=400)

    comment = get_object_or_404(Comment, id=comment_id)

    reaction, created = CommentReaction.objects.get_or_create(
        user=request.user, comment=comment, defaults={"reaction": reaction_type}
    )

    removed = False

    if not created:
        if reaction.reaction == reaction_type:
            reaction.delete()
            removed = True
        else:
            reaction.reaction = reaction_type
            reaction.save()

    if not removed and comment.user != request.user:
        Notification.objects.create(
            actor=request.user,
            user=comment.user,
            verb="reaccionó a tu comentario",
            target_type="comment",
            target_id=comment.id,
            reaction=reaction_type,
        )

    counts = _counts_por_reaccion(comment)
    total = sum(counts.values())

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "reactions",
        {
            "type": "reaction_update",
            "data": {
                "object_type": "comment",
                "id": comment.id,
                "count": total,
            },
        },
    )

    return JsonResponse(
        {
            "removed": removed,
            "reaction": reaction_type,
            "counts": counts,
            "count": total,
        }
    )


@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.user != request.user:
        return JsonResponse({"error": "No autorizado"}, status=403)

    comment.delete()
    return JsonResponse({"success": True})


@login_required
def comment_reactions_list(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    totals = _counts_por_reaccion(comment)

    users_data = []

    for r in comment.reactions.select_related("user").order_by("-created_at"):
        user = r.user
        profile_url = reverse("profile", args=[user.username])

        avatar = (
            request.build_absolute_uri(user.profile.image.url)
            if hasattr(user, "profile") and user.profile.image
            else request.build_absolute_uri("/static/img/default_profile.jpg")
        )

        users_data.append(
            {
                "username": user.username,
                "profile_url": profile_url,
                "avatar_url": avatar,
                "reaction": r.reaction,
            }
        )

    return JsonResponse({"totals": totals, "users": users_data})