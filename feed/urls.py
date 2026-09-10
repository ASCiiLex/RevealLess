from django.urls import path
from .views import feed_view, feed_react_view

urlpatterns = [
    path('', feed_view, name='feed'),
    path('react/', feed_react_view, name='feed_react'),
]