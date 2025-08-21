from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Notification
import json
import asyncio

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        print(self.user)

        if self.user.is_anonymous:
            await self.close()
        
        else:
            
            self.group_name = f'notification_{self.user.id}'

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            print(self.group_name)
            await self.accept()



    async def disconnect(self, code):
        if hasattr(self,'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )


    @database_sync_to_async
    def delevere_notification(self,notification):
        print(notification)
        try:
            notification = Notification.objects.get(id = notification['id'])
            notification.is_delevered = True
            notification.save()
            print('isdelvered done!!')
        except:
            pass

    async def send_notification(self,event):
        print('trying send notification from the consumer')
        notification = event['notification']
        await self.send(text_data=json.dumps(notification))
        print('send() method has ran')
        await self.delevere_notification(notification)
        print('isdelevered method ran')
        