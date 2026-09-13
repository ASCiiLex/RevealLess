from django.urls import path
from .views import (
    profile_view, search_view, followers_view, following_view, edit_profile,
    profile_react_view, edit_profile_react_view,
)
from .api_views import ProfileDetailAPIView, ProfileEditAPIView

urlpatterns = [
    path('buscar/', search_view, name='search'),

    path('editar/', edit_profile, name='edit_profile'),
    path('editar-react/', edit_profile_react_view, name='edit_profile_react'),

    path('api/editar/', ProfileEditAPIView.as_view(), name='profiles_api_edit'),
    path('api/<str:username>/', ProfileDetailAPIView.as_view(), name='profiles_api_detail'),

    # Listas
    path('<str:username>/seguidores/', followers_view, name='followers'),
    path('<str:username>/seguidos/', following_view, name='following'),

    # Perfil
    path('<str:username>/react/', profile_react_view, name='profile_react'),
    path('<str:username>/', profile_view, name='profile'),
]