from django.urls import re_path
from notifications.consumers import NotificationConsumer
from messages_app.consumers import ChatConsumer, MessagesAlertConsumer
from likes.consumers import ReactionConsumer

websocket_urlpatterns = [
    re_path(r"^ws/notifications/$", NotificationConsumer.as_asgi()),
    re_path(r"^ws/chat/(?P<username>\w+)/$", ChatConsumer.as_asgi()),
    re_path(r"^ws/reactions/$", ReactionConsumer.as_asgi()),
    re_path(r"^ws/messages/$", MessagesAlertConsumer.as_asgi()),
]