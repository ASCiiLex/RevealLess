from django.shortcuts import render, get_object_or_404
from django.db.models import Count

from comments.models import Comment, CommentReaction
from likes.models import PostReaction
from ..models import Post


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    sort = request.GET.get('sort', 'recent')

    comments = get_sorted_comments(post, sort)
    post_reaction = apply_user_reactions(request, comments, post)

    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': comments,
        'current_sort': sort,
        'post_reaction': post_reaction,
    })


def get_sorted_comments(post, sort):
    qs = Comment.objects.filter(
        post=post,
        parent__isnull=True
    ).prefetch_related(
        'replies',
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


def apply_user_reactions(request, comments, post):
    if not request.user.is_authenticated:
        for c in comments:
            c.user_reaction = None
            for r in c.replies.all():
                r.user_reaction = None
        return None

    reactions = CommentReaction.objects.filter(
        user=request.user,
        comment__post=post
    ).values('comment_id', 'reaction')

    reaction_map = {r['comment_id']: r['reaction'] for r in reactions}

    for c in comments:
        c.user_reaction = reaction_map.get(c.id)
        for r in c.replies.all():
            r.user_reaction = reaction_map.get(r.id)

    pr = PostReaction.objects.filter(
        user=request.user,
        post=post
    ).first()

    return pr.reaction if pr else None