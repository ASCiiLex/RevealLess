from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse

from posts.models import Post
from .models import PostReaction


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

    if not created:
        if reaction.reaction == reaction_type:
            reaction.delete()
            return JsonResponse({'removed': True})
        reaction.reaction = reaction_type
        reaction.save()

    return JsonResponse({
        'removed': False,
        'reaction': reaction_type,
        'counts': {
            'like': post.reactions.filter(reaction='like').count(),
            'love': post.reactions.filter(reaction='love').count(),
            'funny': post.reactions.filter(reaction='funny').count(),
            'wow': post.reactions.filter(reaction='wow').count(),
            'sad': post.reactions.filter(reaction='sad').count(),
        }
    })


@login_required
def post_reactions_list(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    users_data = []

    for r in post.reactions.select_related('user').order_by('-created_at'):
        user = r.user
        profile_url = reverse('profile', args=[user.username])

        avatar = (
            request.build_absolute_uri(user.profile.image.url)
            if hasattr(user, 'profile') and user.profile.image
            else request.build_absolute_uri('/static/img/default_profile.jpg')
        )

        users_data.append({
            'username': user.username,
            'profile_url': profile_url,
            'avatar_url': avatar,
            'reaction': r.reaction,
        })

    return JsonResponse({'users': users_data})