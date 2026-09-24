from datetime import timedelta

from django.shortcuts import render
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Count

from ..models import Hashtag, Post


def hashtag_detail(request, name):
    name = name.lower().strip()

    hashtag = Hashtag.objects.filter(name=name).first()

    # Solo posts visibles según el progreso del usuario (anónimo: ninguno).
    if hashtag:
        posts_qs = (
            Post.objects.visible_for(request.user)
            .filter(post_hashtags__hashtag=hashtag)
            .select_related('author')
            .distinct()
            .order_by('-created_at')
        )
    else:
        posts_qs = Post.objects.none()

    paginator = Paginator(posts_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Trending hashtags (últimos 7 días)
    since = timezone.now() - timedelta(days=7)

    trending_hashtags = Hashtag.objects.filter(
        posts__post__created_at__gte=since
    ).annotate(
        num_posts=Count('posts__post', distinct=True)
    ).order_by('-num_posts')[:10]

    context = {
        'hashtag': hashtag if hashtag else {'name': name},
        'posts': page_obj,
        'page_obj': page_obj,
        'trending_hashtags': trending_hashtags,
    }

    return render(request, 'posts/hashtag_detail.html', context)