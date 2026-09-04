from django.urls import path
from .views import inbox_view, chat_view

urlpatterns = [
    path('', inbox_view, name='inbox'),
    path('<str:username>/', chat_view, name='chat'),
]