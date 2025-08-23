from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json 
from .models import ChatMessage,ChatRoom
from main_app.models import Profile,User

class UserChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print('user: ',self.scope['user'])
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()

        self.user_profile = await self.get_profile(self.user)

        self.room_id = self.scope['url_route']['kwargs']['room_id']
        print(self.room_id)
        self.room_group_name = f'chatRoom-{self.room_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, code):
        if hasattr(self,'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )


    async def receive(self,text_data):
        text_json_data = json.loads(text_data)
        message = text_json_data['message']

        print(message)

        room = await self.get_room()
        if await self.is_user_in_room():
            message_obj = await self.create_message(room,message)

            #send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type':'chat_message',
                    'message':message,
                    'sender_id':message_obj.sender.id,
                    'sender_username':self.user.username,
                    'timestamp':str(message_obj.timestamp)
                }
            )


    #receive message from room group
    async def chat_message(self,event):
        message = event['message']
        sender_id = event['sender_id']
        sender_username = event['sender_username']
        timestamp = event['timestamp']

        #send message to websocket
        await self.send(
            text_data = json.dumps(
                {
                    'message':message,
                    'sender_id':sender_id,
                    'sender_username':sender_username,
                    'timestamp':timestamp
                }
        )
        )

    @database_sync_to_async
    def get_room(self):
        return ChatRoom.objects.get(id = self.room_id)
    
    @database_sync_to_async
    def get_profile(self,user):
        return Profile.objects.get(user = user)

    @database_sync_to_async
    def is_user_in_room(self):
        room_id = int(self.room_id)
        return ChatRoom.objects.filter(
            id = room_id,
            participants = self.user_profile).exists()
    

    @database_sync_to_async
    def create_message(self,room,msg):
        return ChatMessage.objects.create(
            room = room,
            sender = self.user_profile,
            message = msg
        )
        