from django.urls import path
from .views import (
    add_comment,
    toggle_reaction_comment,
    delete_comment,
    comment_reactions_list,
)

urlpatterns = [
    path('add/', add_comment, name='add_comment'),
    path('react/<int:comment_id>/', toggle_reaction_comment, name='toggle_reaction_comment'),
    path('delete/<int:comment_id>/', delete_comment, name='delete_comment'),
    path('reactions/<int:comment_id>/', comment_reactions_list, name='comment_reactions_list'),
]