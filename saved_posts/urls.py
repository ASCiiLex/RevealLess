from django.urls import path
from .views import save_post, unsave_post, saved_posts_view

urlpatterns = [
    path('guardar/<int:post_id>/', save_post, name='save_post'),
    path('desguardar/<int:post_id>/', unsave_post, name='unsave_post'),
    path('guardados/', saved_posts_view, name='saved_posts'),
]