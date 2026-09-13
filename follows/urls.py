from django.urls import path
from .views import (
    follow_user, unfollow_user, followers_list, following_list,
    followers_react_view, following_react_view,
)
from .api_views import FollowToggleAPIView, FollowersListAPIView, FollowingListAPIView

urlpatterns = [
    path('follow/<str:username>/', follow_user, name='follow'),
    path('unfollow/<str:username>/', unfollow_user, name='unfollow'),
    path('seguidores/<str:username>/', followers_list, name='followers_list'),
    path('siguiendo/<str:username>/', following_list, name='following_list'),

    path('seguidores-react/<str:username>/', followers_react_view, name='followers_react'),
    path('siguiendo-react/<str:username>/', following_react_view, name='following_react'),

    path('api/<str:username>/', FollowToggleAPIView.as_view(), name='follows_api_toggle'),
    path('api/<str:username>/seguidores/', FollowersListAPIView.as_view(), name='follows_api_followers'),
    path('api/<str:username>/siguiendo/', FollowingListAPIView.as_view(), name='follows_api_following'),
]