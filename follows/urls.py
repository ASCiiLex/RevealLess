from django.urls import path
from .views import follow_user, unfollow_user, followers_list, following_list

urlpatterns = [
    path('follow/<str:username>/', follow_user, name='follow'),
    path('unfollow/<str:username>/', unfollow_user, name='unfollow'),
    path('seguidores/<str:username>/', followers_list, name='followers_list'),
    path('siguiendo/<str:username>/', following_list, name='following_list'),
]