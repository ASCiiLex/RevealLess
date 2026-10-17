import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Antes de importar nada que cargue modelos (routing -> consumers).
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

import core.routing  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    # Rechaza WebSockets abiertos desde otros orígenes (cross-site WebSocket hijacking).
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter(core.routing.websocket_urlpatterns))
    ),
})