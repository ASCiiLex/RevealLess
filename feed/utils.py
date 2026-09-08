from django.db.models import Count, Prefetch
from posts.models import Post
from comments.models import Comment, CommentReaction
from likes.models import PostReaction


def get_user_feed(user):
    followed_users = user.following.values_list('followed', flat=True)

    visible_comments = Comment.objects.visible_for(user).select_related("user")
    comment_reactions_qs = CommentReaction.objects.select_related("user")
    reactions_qs = PostReaction.objects.select_related("user")

    return (
        Post.objects
        .filter(author__in=followed_users)
        .select_related("author")
        .prefetch_related(
            Prefetch("comments", queryset=visible_comments),
            Prefetch("comments__replies", queryset=visible_comments),
            Prefetch("comments__reactions", queryset=comment_reactions_qs),
            Prefetch("reactions", queryset=reactions_qs),
            "post_hashtags__hashtag",
        )
        .annotate(
            likes_total=Count("reactions", distinct=True),
            comments_total=Count("comments", distinct=True),
        )
        .order_by("-created_at")
    )