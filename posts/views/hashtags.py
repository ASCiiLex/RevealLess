from datetime import timedelta

from django.shortcuts import render
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Count

from ..models import Hashtag, Post


def hashtag_detail(request, name):
    # 🔥 Normalización (clave para evitar errores)
    name = name.lower().strip()

    # 🔍 Buscar hashtag sin romper
    hashtag = Hashtag.objects.filter(name=name).first()

    # 🔥 Query de posts (vacío si no existe hashtag)
    if hashtag:
        posts_qs = Post.objects.filter(
            post_hashtags__hashtag=hashtag
        ).select_related('author').distinct().order_by('-created_at')
    else:
        posts_qs = Post.objects.none()

    # 📄 Paginación segura
    paginator = Paginator(posts_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 🔥 Trending hashtags (últimos 7 días)
    since = timezone.now() - timedelta(days=7)

    trending_hashtags = Hashtag.objects.filter(
        posts__post__created_at__gte=since
    ).annotate(
        num_posts=Count('posts__post', distinct=True)
    ).order_by('-num_posts')[:10]

    # 🧠 Contexto consistente SIEMPRE
    context = {
        'hashtag': hashtag if hashtag else {'name': name},
        'posts': page_obj,
        'page_obj': page_obj,
        'trending_hashtags': trending_hashtags,
    }

    return render(request, 'posts/hashtag_detail.html', context)