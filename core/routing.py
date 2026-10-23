from django.urls import re_path
from notifications.consumers import NotificationConsumer
from messages_app.consumers import ChatConsumer, MessagesAlertConsumer

websocket_urlpatterns = [
    re_path(r"^ws/notifications/$", NotificationConsumer.as_asgi()),
    # Misma regla que accounts.validators: letras sin acentos, cifras y _.
    re_path(r"^ws/chat/(?P<username>[A-Za-z0-9_]+)/$", ChatConsumer.as_asgi()),
    re_path(r"^ws/messages/$", MessagesAlertConsumer.as_asgi()),
]