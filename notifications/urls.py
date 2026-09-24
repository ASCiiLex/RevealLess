from django.urls import path
from .views import post_not_found_view, notifications_react_view
from .api_views import NotificationListAPIView

urlpatterns = [
    path("post-no-existe/<int:notif_id>/", post_not_found_view, name="post_not_found"),

    path('react/', notifications_react_view, name='notifications_react'),
    path('api/', NotificationListAPIView.as_view(), name='notifications_api_list'),
]