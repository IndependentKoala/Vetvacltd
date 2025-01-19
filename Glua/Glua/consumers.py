# consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.generic.websocket import WebsocketConsumer
import json

class UserStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Create or join a group for user status updates
        self.room_group_name = 'user_status_group'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Remove from the group on disconnect
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Receive message from WebSocket
        data = json.loads(text_data)
        status = data['status']
        user = data['user']

        # Broadcast the status change to all clients in the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status_update',
                'status': status,
                'user': user
            }
        )

    # Handle broadcasted messages to all clients
    async def user_status_update(self, event):
        status = event['status']
        user = event['user']

        # Send status update to WebSocket
        await self.send(text_data=json.dumps({
            'status': status,
            'user': user
        }))
class UserStatusConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        data = json.loads(text_data)
        username = data['user']
        status = data['status']
        
        # Broadcast the status change to all connected clients
        self.send(text_data=json.dumps({
            'user': username,
            'status': status
        }))