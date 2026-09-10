from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.shortcuts import redirect
from django.views.static import serve

from .api_views import MeAPIView


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('feed')
    return redirect('login')


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home_redirect, name='home'),

    path('cuentas/', include('accounts.urls')),
    path('feed/', include('feed.urls')),
    path('perfil/', include('profiles.urls')),
    path('posts/', include('posts.urls')),
    path('follows/', include('follows.urls')),
    path('comments/', include('comments.urls')),
    path('notificaciones/', include('notifications.urls')),
    path('mensajes/', include('messages_app.urls')),
    path('guardados/', include('saved_posts.urls')),
    path('narrative/', include('narrative.urls')),

    path('api/me/', MeAPIView.as_view(), name='api_me'),
]

if settings.SERVE_MEDIA:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT
        }),
    ]