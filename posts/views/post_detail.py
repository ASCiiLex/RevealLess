from django.shortcuts import redirect, get_object_or_404, render
from django.db.models import Count, Prefetch

from comments.models import Comment
from ..models import Post


def post_detail(request, post_id):
    return redirect('post_detail_react', post_id=post_id)


def get_sorted_comments(user, post, sort):
    visible_replies = Comment.objects.visible_for(user)

    qs = Comment.objects.visible_for(user).filter(
        post=post,
        parent__isnull=True
    ).prefetch_related(
        Prefetch('replies', queryset=visible_replies),
        'replies__user',
        'replies__reactions',
        'reactions',
        'user'
    )

    if sort == 'oldest':
        return qs.order_by('created_at')

    if sort == 'popular':
        return qs.annotate(
            num_reactions=Count('reactions')
        ).order_by('-num_reactions', '-created_at')

    return qs.order_by('-created_at')


def post_detail_react_view(request, post_id):
    """Monta React para el detalle de post. Sin login: visible_for() filtra
    igual a usuarios autenticados y anónimos."""
    get_object_or_404(Post.objects.visible_for(request.user), id=post_id)
    return render(request, 'posts/post_detail_react.html', {'post_id': post_id})