from django.urls import path
from .views import notifications_view, post_not_found_view

urlpatterns = [
    path('', notifications_view, name='notifications'),
    path("post-no-existe/<int:notif_id>/", post_not_found_view, name="post_not_found"),

]