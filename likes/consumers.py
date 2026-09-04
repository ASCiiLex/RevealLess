import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ReactionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("reactions", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("reactions", self.channel_name)

    async def reaction_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))