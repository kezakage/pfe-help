"""
WebSocket consumer: each authenticated user joins a private group `user_<id>`
and receives notification frames sent via `apps.notifications.utils.push`.
"""
import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationsConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(code=4401)
            return
        self.group_name = f"user_{user.pk}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "ready"})

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Client → server pings (optional)
        if content.get("type") == "ping":
            await self.send_json({"type": "pong"})

    # Handler for messages dispatched via group_send(type="notify")
    async def notify(self, event):
        await self.send_json({"type": "notification", "data": event["data"]})
