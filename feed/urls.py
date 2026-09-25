from django.urls import path
from django.shortcuts import redirect
from .views import feed_view, feed_react_view


def feed_react_legacy_redirect(request):
    """Compatibilidad: /feed/react/ ya no existe como ruta propia (se
    renombró a / en la limpieza de rutas), pero puede seguir marcada
    en favoritos o compartida en enlaces antiguos."""
    if request.user.is_authenticated:
        return redirect('feed')
    return redirect('feed_publico')


urlpatterns = [
    path('publica/', feed_view, name='feed_publico'),
    path('react/', feed_react_legacy_redirect, name='feed_react_legacy'),
    path('', feed_react_view, name='feed'),
]