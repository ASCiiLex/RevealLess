from django.urls import path
from .views import inbox_view, chat_view, inbox_react_view, chat_react_view
from .api_views import InboxListAPIView, ChatHistoryAPIView

urlpatterns = [
    path('', inbox_view, name='inbox'),
    path('react/', inbox_react_view, name='inbox_react'),

    path('api/', InboxListAPIView.as_view(), name='messages_api_inbox'),
    path('api/<str:username>/', ChatHistoryAPIView.as_view(), name='messages_api_chat'),

    path('chat-react/<str:username>/', chat_react_view, name='chat_react'),
    path('<str:username>/', chat_view, name='chat'),
]