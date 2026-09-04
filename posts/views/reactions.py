from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from likes.models import PostReaction
from notifications.models import Notification
from ..models import Post


@login_required
@require_POST
def toggle_reaction_post(request):
    post_id = request.POST.get('post_id')
    reaction_type = request.POST.get('reaction')

    post = get_object_or_404(Post, id=post_id)

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

    if not removed and post.author != request.user:
        Notification.objects.create(
            actor=request.user,
            user=post.author,
            verb="reaccionó a tu post",
            target_type="post",
            target_id=post.id,
            reaction=reaction_type
        )

    counts = {
        'like': post.reactions.filter(reaction='like').count(),
        'love': post.reactions.filter(reaction='love').count(),
        'funny': post.reactions.filter(reaction='funny').count(),
        'wow': post.reactions.filter(reaction='wow').count(),
        'sad': post.reactions.filter(reaction='sad').count(),
    }
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
    post = get_object_or_404(Post, id=post_id)

    totals = {
        'like': post.reactions.filter(reaction='like').count(),
        'love': post.reactions.filter(reaction='love').count(),
        'funny': post.reactions.filter(reaction='funny').count(),
        'wow': post.reactions.filter(reaction='wow').count(),
        'sad': post.reactions.filter(reaction='sad').count(),
    }

    users_data = []

    for r in post.reactions.select_related('user').order_by('-created_at'):
        user = r.user
        profile_url = reverse('profile', args=[user.username])

        avatar = (
            request.build_absolute_uri(user.profile.image.url)
            if hasattr(user, "profile") and user.profile.image
            else request.build_absolute_uri("/static/img/default_profile.jpg")
        )

        users_data.append({
            'username': user.username,
            'profile_url': profile_url,
            'avatar_url': avatar,
            'reaction': r.reaction,
        })

    return JsonResponse({
        'totals': totals,
        'users': users_data
    })