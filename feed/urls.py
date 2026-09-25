from django.urls import path
from .views import feed_view, feed_react_view

urlpatterns = [
    path('publica/', feed_view, name='feed_publico'),
    path('', feed_react_view, name='feed'),
]