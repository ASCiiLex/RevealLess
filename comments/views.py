from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from narrative.models import ClasificacionNarrativa
from posts.models import Post
from .models import Comment, CommentReaction
from .serializers import CommentCreateSerializer, CommentUpdateSerializer
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

    entrada = CommentCreateSerializer(data=request.POST)
    if not entrada.is_valid():
        primer_error = next(iter(entrada.errors.values()))[0]
        return JsonResponse({"error": str(primer_error)}, status=400)

    datos = entrada.validated_data
    text = datos["text"].strip()
    if not text:
        return JsonResponse({"error": "Texto vacío"}, status=400)

    post = get_object_or_404(Post, id=post_id)

    parent = None
    parent_id = datos.get("parent_id")
    if parent_id:
        parent = get_object_or_404(Comment, id=parent_id, post=post)
        # Límite de 3 niveles: comentario -> respuesta -> respuesta-a-
        # respuesta, y ahi se para. Si el padre ya tiene su propio
        # padre (ya es una respuesta), esto seria un nivel 4.
        if parent.parent_id is not None:
            return JsonResponse(
                {"error": "No se puede responder a una respuesta ya anidada."},
                status=400,
            )

    referencia = datos.get("referencia_narrativa") or post.referencia_narrativa
    frontera = datos.get("frontera_spoiler")

    comment = Comment(
        user=request.user, post=post, parent=parent, text=text,
        referencia_narrativa=referencia,
        emocion_autor=datos.get("emocion_autor"),
    )

    if frontera:
        comment.frontera_spoiler = frontera
        comment.frontera_origen = ClasificacionNarrativa.ORIGEN_EXPLICITO
    # Si no se especifica frontera, se queda con el default del modelo
    # (ORIGEN_HEREDADO_POST, frontera_spoiler=None) -- hereda la del
    # post, comportamiento ya existente. Sin asistente de IA para
    # comentarios por ahora (anotado para v2).

    try:
        comment.full_clean()
    except ValidationError as exc:
        return JsonResponse({"error": exc.message_dict}, status=400)

    comment.save()

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
            "referencia_narrativa_id": comment.referencia_narrativa_id,
            "frontera_spoiler_id": comment.frontera_spoiler_id,
            "frontera_origen": comment.frontera_origen,
            "likes_count": 0,
        }
    )


class CommentUpdateAPIView(APIView):
    """Edita un comentario ya publicado. Solo el autor puede editarlo
    (403 si no). Mismo criterio que PostUpdateAPIView: si se envía
    frontera_spoiler, se marca ORIGEN_EXPLICITO; si no se envía, la
    frontera actual no se toca."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)

        if comment.user != request.user:
            return Response(
                {'detail': 'No puedes editar comentarios de otro usuario.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        entrada = CommentUpdateSerializer(data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data

        if 'text' in datos:
            comment.text = datos['text']
        if 'emocion_autor' in datos:
            comment.emocion_autor = datos['emocion_autor']
        if 'referencia_narrativa' in datos:
            comment.referencia_narrativa = datos['referencia_narrativa']
        if 'frontera_spoiler' in datos:
            comment.frontera_spoiler = datos['frontera_spoiler']
            comment.frontera_origen = ClasificacionNarrativa.ORIGEN_EXPLICITO

        try:
            comment.full_clean()
        except ValidationError as exc:
            return Response({'detail': exc.message_dict}, status=status.HTTP_400_BAD_REQUEST)

        comment.save()
        return Response({
            'id': comment.id,
            'text': comment.text,
            'emocion_autor': comment.emocion_autor,
            'referencia_narrativa_id': comment.referencia_narrativa_id,
            'frontera_spoiler_id': comment.frontera_spoiler_id,
            'frontera_origen': comment.frontera_origen,
        })


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