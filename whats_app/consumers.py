import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import *


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'
        self.user = self.scope['user']

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Set user as online
        await self.set_user_online(True)

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Set user as offline
        await self.set_user_online(False)
        
        # Stop typing indicator
        await self.update_typing_status(False)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'chat_message':
            await self.handle_chat_message(data)
        elif message_type == 'typing':
            await self.handle_typing(data)
        elif message_type == 'read_receipt':
            await self.handle_read_receipt(data)
        elif message_type == 'voice_call':
            await self.handle_voice_call(data)
        elif message_type == 'video_call':
            await self.handle_video_call(data)

    async def handle_chat_message(self, data):
        content = data['content']
        message_type = data.get('message_type', 'text')
        reply_to_id = data.get('reply_to')
        
        # Save message to database
        message = await self.save_message(content, message_type, reply_to_id)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': str(message.message_id),
                    'sender': self.user.phone_number,
                    'sender_name': self.user.username,
                    'sender_photo': self.user.profile_picture.url if self.user.profile_picture else None,
                    'content': message.content,
                    'message_type': message.message_type,
                    'timestamp': message.created_at.isoformat(),
                    'is_edited': message.is_edited,
                    'reply_to': str(message.reply_to.message_id) if message.reply_to else None,
                }
            }
        )
        
        # Update message status to delivered
        await self.update_message_status(message, 'delivered')

    async def handle_typing(self, data):
        is_typing = data.get('is_typing', False)
        
        await self.update_typing_status(is_typing)
        
        # Broadcast typing status
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user': self.user.phone_number,
                'is_typing': is_typing
            }
        )

    async def handle_read_receipt(self, data):
        message_id = data.get('message_id')
        
        # Update message status to read
        await self.mark_message_read(message_id)
        
        # Broadcast read receipt
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'read_receipt',
                'message_id': message_id,
                'user': self.user.phone_number
            }
        )

    async def handle_voice_call(self, data):
        action = data.get('action')  # 'start', 'answer', 'end'
        
        if action == 'start':
            call = await self.start_call('voice')
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'voice_call',
                    'action': 'incoming',
                    'call_id': str(call.call_id),
                    'caller': self.user.phone_number
                }
            )
        elif action == 'answer':
            call_id = data.get('call_id')
            await self.answer_call(call_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'voice_call',
                    'action': 'answered',
                    'call_id': call_id
                }
            )
        elif action == 'end':
            call_id = data.get('call_id')
            await self.end_call(call_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'voice_call',
                    'action': 'ended',
                    'call_id': call_id
                }
            )

    async def handle_video_call(self, data):
        action = data.get('action')  # 'start', 'answer', 'end'
        
        if action == 'start':
            call = await self.start_call('video')
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'video_call',
                    'action': 'incoming',
                    'call_id': str(call.call_id),
                    'caller': self.user.phone_number
                }
            )
        elif action == 'answer':
            call_id = data.get('call_id')
            await self.answer_call(call_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'video_call',
                    'action': 'answered',
                    'call_id': call_id
                }
            )
        elif action == 'end':
            call_id = data.get('call_id')
            await self.end_call(call_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'video_call',
                    'action': 'ended',
                    'call_id': call_id
                }
            )

    # Receive message from room group
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def typing_indicator(self, event):
        # Don't send typing indicator to the user who is typing
        if event['user'] != self.user.phone_number:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user': event['user'],
                'is_typing': event['is_typing']
            }))

    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user': event['user']
        }))

    async def voice_call(self, event):
        await self.send(text_data=json.dumps({
            'type': 'voice_call',
            'action': event['action'],
            'call_id': event.get('call_id'),
            'caller': event.get('caller')
        }))

    async def video_call(self, event):
        await self.send(text_data=json.dumps({
            'type': 'video_call',
            'action': event['action'],
            'call_id': event.get('call_id'),
            'caller': event.get('caller')
        }))

    # Database operations
    @database_sync_to_async
    def save_message(self, content, message_type, reply_to_id):
        chat = Chat.objects.get(chat_id=self.chat_id)
        
        reply_to = None
        if reply_to_id:
            reply_to = Message.objects.get(message_id=reply_to_id)
        
        message = Message.objects.create(
            chat=chat,
            sender=self.user,
            content=content,
            message_type=message_type,
            reply_to=reply_to
        )
        
        # Create status for all participants except sender
        participants = chat.participants.exclude(user=self.user)
        for participant in participants:
            MessageStatus.objects.create(
                message=message,
                user=participant.user,
                status='sent'
            )
        
        return message

    @database_sync_to_async
    def update_message_status(self, message, status):
        MessageStatus.objects.filter(
            message=message
        ).exclude(user=self.user).update(status=status, timestamp=timezone.now())

    @database_sync_to_async
    def mark_message_read(self, message_id):
        message = Message.objects.get(message_id=message_id)
        MessageStatus.objects.filter(
            message=message,
            user=self.user
        ).update(status='read', timestamp=timezone.now())

    @database_sync_to_async
    def update_typing_status(self, is_typing):
        chat = Chat.objects.get(chat_id=self.chat_id)
        TypingStatus.objects.update_or_create(
            chat=chat,
            user=self.user,
            defaults={'is_typing': is_typing}
        )

    @database_sync_to_async
    def set_user_online(self, is_online):
        self.user.is_online = is_online
        if not is_online:
            self.user.last_seen = timezone.now()
        self.user.save()

    @database_sync_to_async
    def start_call(self, call_type):
        chat = Chat.objects.get(chat_id=self.chat_id)
        call = Call.objects.create(
            chat=chat,
            caller=self.user,
            call_type=call_type,
            status='initiated'
        )
        
        # Add all participants
        participants = chat.participants.all()
        for participant in participants:
            CallParticipant.objects.create(
                call=call,
                user=participant.user
            )
        
        return call

    @database_sync_to_async
    def answer_call(self, call_id):
        call = Call.objects.get(call_id=call_id)
        call.status = 'answered'
        call.answered_at = timezone.now()
        call.save()
        
        # Update participant
        CallParticipant.objects.filter(
            call=call,
            user=self.user
        ).update(joined_at=timezone.now())

    @database_sync_to_async
    def end_call(self, call_id):
        call = Call.objects.get(call_id=call_id)
        call.status = 'ended'
        call.ended_at = timezone.now()
        
        if call.answered_at:
            duration = (call.ended_at - call.answered_at).seconds
            call.duration = duration
        
        call.save()
        
        # Update participant
        CallParticipant.objects.filter(
            call=call,
            user=self.user
        ).update(left_at=timezone.now())


class AIConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for AI chat"""
    
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'ai_{self.conversation_id}'
        self.user = self.scope['user']

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
        message_type = data.get('type')

        if message_type == 'ai_message':
            content = data['content']
            
            # Save user message
            await self.save_ai_message(content, True)
            
            # Generate AI response
            ai_response = await self.generate_ai_response(content)
            
            # Save AI message
            await self.save_ai_message(ai_response, False)
            
            # Send to user
            await self.send(text_data=json.dumps({
                'type': 'ai_message',
                'content': ai_response,
                'timestamp': timezone.now().isoformat()
            }))

    @database_sync_to_async
    def save_ai_message(self, content, is_user):
        conversation = AIConversation.objects.get(conversation_id=self.conversation_id)
        AIMessage.objects.create(
            conversation=conversation,
            is_user=is_user,
            content=content
        )

    @database_sync_to_async
    def generate_ai_response(self, user_message):
        """Generate AI response - integrate with Claude API"""
        # This would call Anthropic's API
        # For demo purposes:
        responses = [
            "That's interesting! Tell me more.",
            "I understand. How does that make you feel?",
            "I'm here to chat! What else is on your mind?",
            "That's a great question! Let me think about that...",
        ]
        import random
        return random.choice(responses)