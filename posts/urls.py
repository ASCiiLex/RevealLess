from django.urls import path

from .views.create import create_post
from .views.hashtags import hashtag_detail
from .views.post_detail import post_detail
from .views.reactions import post_reactions_list, toggle_reaction_post
from .views.search import (
    mentions_search,
    hashtags_search,
    suggested_hashtags,
    global_search,
)

urlpatterns = [
    path('<int:post_id>/', post_detail, name='post_detail'),
    path('crear/<slug:obra_slug>/', create_post, name='create_post'),
    path('react/', toggle_reaction_post, name='toggle_reaction_post'),
    path('reactions/<int:post_id>/', post_reactions_list, name='post_reactions_list'),

    path('hashtag/<str:name>/', hashtag_detail, name='hashtag_detail'),

    path('mentions-search/', mentions_search, name='mentions_search'),
    path('hashtags-search/', hashtags_search, name='hashtags_search'),
    path('suggested-hashtags/', suggested_hashtags, name='suggested_hashtags'),
    path('search/', global_search, name='global_search'),
]