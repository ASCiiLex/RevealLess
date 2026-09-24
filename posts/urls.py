from django.urls import path

from .views.create import publicar_react_view
from .views.hashtags import hashtag_detail
from .views.post_detail import post_detail, post_detail_react_view
from .views.reactions import post_reactions_list, toggle_reaction_post
from .views.search import (
    mentions_search,
    hashtags_search,
    suggested_hashtags,
    global_search,
)
from .api_views import PostCreateAPIView, PostDetailAPIView, PostUpdateAPIView

urlpatterns = [
    path('<int:post_id>/', post_detail, name='post_detail'),
    path('<int:post_id>/react/', post_detail_react_view, name='post_detail_react'),
    path('crear-react/', publicar_react_view, name='publicar_react'),
    path('api/crear/<slug:obra_slug>/', PostCreateAPIView.as_view(), name='posts_api_create'),
    path('api/<int:post_id>/', PostDetailAPIView.as_view(), name='posts_api_detail'),
    path('api/<int:post_id>/editar/', PostUpdateAPIView.as_view(), name='posts_api_update'),
    path('react/', toggle_reaction_post, name='toggle_reaction_post'),
    path('reactions/<int:post_id>/', post_reactions_list, name='post_reactions_list'),

    path('hashtag/<str:name>/', hashtag_detail, name='hashtag_detail'),

    path('mentions-search/', mentions_search, name='mentions_search'),
    path('hashtags-search/', hashtags_search, name='hashtags_search'),
    path('suggested-hashtags/', suggested_hashtags, name='suggested_hashtags'),
    path('search/', global_search, name='global_search'),
]