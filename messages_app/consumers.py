import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User

from .models import Message
from .salas import sala_chat

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    # Sin sala hasta que connect acepta: disconnect también llega tras un rechazo.
    room_name = None

    async def connect(self):
        self.user = self.scope["user"]
        self.other_username = self.scope["url_route"]["kwargs"]["username"]

        if not self.user.is_authenticated:
            await self.close()
            return

        if not await self.other_user_exists(self.other_username):
            await self.close()
            return

        self.room_name = sala_chat(self.user.username, self.other_username)

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        logger.info("ChatConsumer connect %s -> %s", self.user.username, self.room_name)

    async def disconnect(self, close_code):
        if self.room_name:
            await self.channel_layer.group_discard(self.room_name, self.channel_name)
        logger.info("ChatConsumer disconnect %s", self.user.username)

    async def receive(self, text_data=None, bytes_data=None):
        # Solo JSON con un texto no vacío; lo demás se ignora sin cerrar la conexión.
        try:
            data = json.loads(text_data or '')
        except json.JSONDecodeError:
            return
        texto = data.get("text") if isinstance(data, dict) else None
        if not isinstance(texto, str) or not texto.strip():
            return

        message = await self.create_message(
            self.user.username,
            self.other_username,
            texto.strip(),
        )

        payload = {
            "id": message.id,
            "text": message.text,
            "sender": message.sender.username,
            "created_at": message.created_at.isoformat(),
            "reaccion": None,
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

    async def reaction_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "reaction",
            **event["data"],
        }))

    @database_sync_to_async
    def other_user_exists(self, username):
        return User.objects.filter(username=username).exists()

    @database_sync_to_async
    def create_message(self, sender_username, receiver_username, text):
        sender = User.objects.get(username=sender_username)
        receiver = User.objects.get(username=receiver_username)
        return Message.objects.create(sender=sender, receiver=receiver, text=text)


class MessagesAlertConsumer(AsyncWebsocketConsumer):
    group_name = None

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
        if self.group_name:
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