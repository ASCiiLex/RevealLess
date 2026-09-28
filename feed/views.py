from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import redirect, render

from narrative.models import Obra
from posts.models import Post

OBRAS_ADELANTO = 6
OBRAS_POR_TANDA = 12  # Divisible entre 6, 3 y 2 columnas.


def _obras_por_actividad():
    # 'id' desempata para que la paginación sea estable.
    return Obra.objects.annotate(posts_total=Count('posts')).order_by('-posts_total', 'titulo', 'id')


def _stats_publicas():
    return {
        'obras_count': Obra.objects.count(),
        'posts_count': Post.objects.count(),
        'usuarios_count': User.objects.count(),
    }


def feed_view(request):
    if request.user.is_authenticated:
        return redirect('feed')

    # Escaparate para visitantes: solo agregados y portadas, sin contenido narrativo.
    return render(request, 'feed/public_landing.html', {
        'obras': _obras_por_actividad()[:OBRAS_ADELANTO],
        'stats': _stats_publicas(),
    })


def catalogo_publico_view(request):
    paginator = Paginator(_obras_por_actividad(), OBRAS_POR_TANDA)
    pagina = paginator.get_page(request.GET.get('pagina'))
    contexto = {'pagina': pagina, 'total_obras': paginator.count}

    # "Ver más": solo las tarjetas de la tanda pedida; la siguiente viaja en cabecera.
    if request.GET.get('parcial') == '1':
        response = render(request, 'feed/_catalogo_tarjetas.html', contexto)
        response['X-Pagina-Siguiente'] = str(pagina.next_page_number()) if pagina.has_next() else ''
        return response

    return render(request, 'feed/catalogo_publico.html', contexto)


@login_required
def feed_react_view(request):
    """Monta el punto de entrada de React (Fase 4). Los datos vienen de narrative/api/."""
    return render(request, 'feed/feed_react.html')