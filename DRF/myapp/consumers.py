import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import DirectMessage, ChatSession, ChatMessage

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '')
        message_type = data.get('type', 'direct')

        if message_type == 'direct':
            recipient_id = data.get('recipient_id')
            if recipient_id:
                await self.save_direct_message(recipient_id, message)
                await self.channel_layer.group_send(
                    f'user_{recipient_id}',
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender_id': self.user.id,
                        'sender_name': self.user.username,
                    }
                )
        elif message_type == 'session':
            session_id = data.get('session_id')
            if session_id:
                await self.save_session_message(session_id, message)
                await self.channel_layer.group_send(
                    f'session_{session_id}',
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender_id': self.user.id,
                        'sender_name': self.user.username,
                    }
                )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
        }))

    @database_sync_to_async
    def save_direct_message(self, recipient_id, content):
        try:
            recipient = User.objects.get(id=recipient_id)
            DirectMessage.objects.create(
                sender=self.user,
                recipient=recipient,
                content=content
            )
        except User.DoesNotExist:
            pass

    @database_sync_to_async
    def save_session_message(self, session_id, content):
        try:
            session = ChatSession.objects.get(id=session_id, user=self.user)
            ChatMessage.objects.create(
                session=session,
                role='user',
                content=content
            )
        except ChatSession.DoesNotExist:
            pass


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        self.user_group_name = f'user_{self.user.id}'

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': event.get('notification_type', 'info'),
            'title': event.get('title', ''),
            'message': event.get('message', ''),
            'data': event.get('data', {}),
        }))