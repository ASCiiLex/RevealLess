import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User

from .models import Message

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]
        self.other_username = self.scope["url_route"]["kwargs"]["username"]

        if not self.user.is_authenticated:
            await self.close()
            return

        if not await self.other_user_exists(self.other_username):
            await self.close()
            return

        usernames = sorted([self.user.username, self.other_username])
        self.room_name = f"chat_{usernames[0]}_{usernames[1]}"

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        logger.info("ChatConsumer connect %s -> %s", self.user.username, self.room_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)
        logger.info("ChatConsumer disconnect %s", self.user.username)

    async def receive(self, text_data):
        data = json.loads(text_data)
        text = data.get("text", "").strip()
        if not text:
            return

        message = await self.create_message(
            self.user.username,
            self.other_username,
            text
        )

        payload = {
            "text": message.text,
            "sender": message.sender.username,
            "created_at": message.created_at.isoformat(),
        }

        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "chat_message",
                "data": payload,
            },
        )

        logger.info("Mensaje creado %s -> %s", message.sender, message.receiver)

        await self.channel_layer.group_send(
            f"messages_{message.receiver.id}",
            {
                "type": "new_message_alert",
                "count": 1
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["data"]))

    @database_sync_to_async
    def other_user_exists(self, username):
        return User.objects.filter(username=username).exists()

    @database_sync_to_async
    def create_message(self, sender_username, receiver_username, text):
        sender = User.objects.get(username=sender_username)
        receiver = User.objects.get(username=receiver_username)
        return Message.objects.create(sender=sender, receiver=receiver, text=text)


class MessagesAlertConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close()
            return

        self.group_name = f"messages_{user.id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        logger.info("MessagesAlert connect -> %s", self.group_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info("MessagesAlert disconnect -> %s", self.group_name)

    async def new_message_alert(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_message",
            "count": event.get("count", 1)
        }))

    async def reset_alert(self, event):
        await self.send(text_data=json.dumps({
            "type": "reset"
        }))