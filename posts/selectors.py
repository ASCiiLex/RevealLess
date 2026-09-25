from django.db.models import Count, Prefetch

from comments.models import Comment


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