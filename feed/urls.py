from django.urls import path
from django.shortcuts import redirect
from .views import catalogo_publico_view, feed_view, feed_react_view


def feed_react_legacy_redirect(request):
    """Compatibilidad: /feed/react/ se renombró a / en la limpieza de rutas,
    pero puede seguir en favoritos o enlaces antiguos."""
    if request.user.is_authenticated:
        return redirect('feed')
    return redirect('feed_publico')


urlpatterns = [
    path('publica/', feed_view, name='feed_publico'),
    path('publica/catalogo/', catalogo_publico_view, name='catalogo_publico'),
    path('react/', feed_react_legacy_redirect, name='feed_react_legacy'),
    path('', feed_react_view, name='feed'),
]