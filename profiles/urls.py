from django.urls import path
from .views import profile_view, search_view, followers_view, following_view, edit_profile

urlpatterns = [
    path('buscar/', search_view, name='search'),

    path('editar/', edit_profile, name='edit_profile'),

    # Listas
    path('<str:username>/seguidores/', followers_view, name='followers'),
    path('<str:username>/seguidos/', following_view, name='following'),

    # Perfil
    path('<str:username>/', profile_view, name='profile'),
]