from django.urls import path
from .views import save_post, unsave_post, saved_posts_view, saved_posts_react_view
from .api_views import SavedPostListAPIView, SavedPostToggleAPIView

urlpatterns = [
    path('guardar/<int:post_id>/', save_post, name='save_post'),
    path('desguardar/<int:post_id>/', unsave_post, name='unsave_post'),
    path('guardados/', saved_posts_view, name='saved_posts'),
    path('guardados-react/', saved_posts_react_view, name='saved_posts_react'),

    path('api/', SavedPostListAPIView.as_view(), name='saved_posts_api_list'),
    path('api/<int:post_id>/', SavedPostToggleAPIView.as_view(), name='saved_posts_api_toggle'),
]