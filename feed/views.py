from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import redirect, render

from narrative.models import Obra
from posts.models import Post


def feed_view(request):
    if request.user.is_authenticated:
        return redirect('feed')

    # Visitante sin sesión: catálogo + estadísticas agregadas, sin contenido narrativo.
    obras = list(Obra.objects.annotate(posts_total=Count('posts')).order_by('-posts_total', 'titulo'))
    stats = {
        'obras_count': len(obras),
        'posts_count': Post.objects.count(),
        'usuarios_count': User.objects.count(),
    }

    return render(request, 'feed/public_landing.html', {
        'obras': obras,
        'stats': stats,
    })


@login_required
def feed_react_view(request):
    """Monta el punto de entrada de React (Fase 4). Los datos vienen de narrative/api/."""
    return render(request, 'feed/feed_react.html')