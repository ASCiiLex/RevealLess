from django.urls import path
from .views import inbox_react_view, chat_react_view, toggle_reaction_message
from .api_views import InboxListAPIView, ChatHistoryAPIView

urlpatterns = [
    path('', inbox_react_view, name='inbox'),

    path('api/', InboxListAPIView.as_view(), name='messages_api_inbox'),
    path('api/<str:username>/', ChatHistoryAPIView.as_view(), name='messages_api_chat'),

    path('<int:message_id>/reaction/', toggle_reaction_message, name='toggle_reaction_message'),

    path('<str:username>/', chat_react_view, name='chat'),
]