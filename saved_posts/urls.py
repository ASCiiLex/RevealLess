from django.urls import path
from .views import saved_posts_react_view
from .api_views import SavedPostListAPIView, SavedPostToggleAPIView

urlpatterns = [
    path('', saved_posts_react_view, name='saved_posts'),

    path('api/', SavedPostListAPIView.as_view(), name='saved_posts_api_list'),
    path('api/<int:post_id>/', SavedPostToggleAPIView.as_view(), name='saved_posts_api_toggle'),
]