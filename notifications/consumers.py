import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    # Sin grupo hasta que connect acepta: disconnect también llega tras un rechazo.
    group = None

    async def connect(self):
        user = self.scope["user"]

        if user.is_anonymous:
            await self.close()
            return

        self.group = f"notifications_{user.id}"

        await self.channel_layer.group_add(
            self.group,
            self.channel_name
        )

        await self.accept()

        logger.info("Notification connect -> %s", self.group)

    async def disconnect(self, close_code):
        if self.group:
            await self.channel_layer.group_discard(
                self.group,
                self.channel_name
            )
        logger.info("Notification disconnect -> %s", self.group)

    async def new_notification(self, event):
        data = event.get("data", {})

        await self.send(text_data=json.dumps({
            "id": data.get("id"),
            "actor": data.get("actor"),
            "verb": data.get("verb"),
            "avatar": data.get("avatar"),
            "url": data.get("url"),
            "created_at": data.get("created_at"),
        }))