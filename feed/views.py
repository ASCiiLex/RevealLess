from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q

from .utils import get_user_feed
from likes.models import PostReaction
from posts.models import Post


def feed_view(request):
    if request.user.is_authenticated:

        # 🔥 FEED BASE (lo que ya tienes)
        base_posts = get_user_feed(request.user)

        # 🔥 AÑADIR TUS POSTS (CLAVE)
        own_posts = Post.objects.filter(author=request.user)

        # 🔥 COMBINAR + EVITAR DUPLICADOS
        posts = (base_posts | own_posts).distinct().order_by('-created_at')

        # 🔖 POSTS GUARDADOS
        saved_posts_ids = list(
            request.user.saved_posts.values_list('post_id', flat=True)
        )

        # ❤️ REACCIONES
        reactions = PostReaction.objects.filter(
            user=request.user,
            post__in=posts
        ).values('post_id', 'reaction')

        reaction_map = {r['post_id']: r['reaction'] for r in reactions}

        for p in posts:
            p.user_reaction = reaction_map.get(p.id)

    else:
        posts = Post.objects.none()
        saved_posts_ids = []

    # 📄 PAGINACIÓN
    paginator = Paginator(posts, 12)
    page = request.GET.get('page')
    posts_page = paginator.get_page(page)

    return render(request, 'feed/feed.html', {
        'posts': posts_page,
        'saved_posts_ids': saved_posts_ids,
    })