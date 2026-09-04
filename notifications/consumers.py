from channels.generic.websocket import AsyncWebsocketConsumer
import json


class NotificationConsumer(AsyncWebsocketConsumer):

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

        print(f"🟢 Notification CONNECT -> {self.group}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group,
            self.channel_name
        )
        print(f"🔴 Notification DISCONNECT -> {self.group}")

    async def new_notification(self, event):
        print(f"🔔 NOTIFICACIÓN WS RECIBIDA en {self.group}: {event}")

        data = event.get("data", {})

        await self.send(text_data=json.dumps({
            "id": data.get("id"),
            "actor": data.get("actor"),
            "verb": data.get("verb"),
            "avatar": data.get("avatar"),
            "url": data.get("url"),
            "created_at": data.get("created_at"),
        }))