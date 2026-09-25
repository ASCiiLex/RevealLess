from django.urls import path
from .views import followers_react_view, following_react_view
from .api_views import FollowToggleAPIView, FollowersListAPIView, FollowingListAPIView

urlpatterns = [
    path('<str:username>/seguidores/', followers_react_view, name='followers'),
    path('<str:username>/siguiendo/', following_react_view, name='following'),

    path('api/<str:username>/', FollowToggleAPIView.as_view(), name='follows_api_toggle'),
    path('api/<str:username>/seguidores/', FollowersListAPIView.as_view(), name='follows_api_followers'),
    path('api/<str:username>/siguiendo/', FollowingListAPIView.as_view(), name='follows_api_following'),
]