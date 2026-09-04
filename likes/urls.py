from django.urls import path
from .views import toggle_reaction_post, post_reactions_list

urlpatterns = [
    path('react/', toggle_reaction_post, name='toggle_reaction_post'),
    path('list/<int:post_id>/', post_reactions_list, name='post_reactions_list'),
]