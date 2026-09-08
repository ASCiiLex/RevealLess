from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Count
from django.contrib.auth.models import User

from .utils import get_user_feed
from likes.models import PostReaction
from posts.models import Post
from narrative.models import Obra


def feed_view(request):
    if request.user.is_authenticated:
        base_posts = get_user_feed(request.user)
        own_posts = Post.objects.filter(author=request.user)

        posts = (base_posts | own_posts).distinct().visible_for(request.user).order_by('-created_at')

        saved_posts_ids = list(
            request.user.saved_posts.values_list('post_id', flat=True)
        )

        reactions = PostReaction.objects.filter(
            user=request.user,
            post__in=posts
        ).values('post_id', 'reaction')

        reaction_map = {r['post_id']: r['reaction'] for r in reactions}

        for p in posts:
            p.user_reaction = reaction_map.get(p.id)

        paginator = Paginator(posts, 12)
        page = request.GET.get('page')
        posts_page = paginator.get_page(page)

        return render(request, 'feed/feed.html', {
            'posts': posts_page,
            'saved_posts_ids': saved_posts_ids,
        })

    # Visitante sin sesión: catálogo + estadísticas agregadas, sin contenido narrativo.
    obras = Obra.objects.annotate(posts_total=Count('posts')).order_by('-posts_total', 'titulo')
    stats = {
        'obras_count': obras.count(),
        'posts_count': Post.objects.count(),
        'usuarios_count': User.objects.count(),
    }

    return render(request, 'feed/public_landing.html', {
        'obras': obras,
        'stats': stats,
    })