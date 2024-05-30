from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json

from accounts.models import CustomUser
from friends.models import FriendRequestThread

class ButtonConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'friend_request_%s' % self.room_name
        print(str(self.room_group_name)+"yo ma ho ")
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        await self.channel_layer.group_send(
            self.room_group_name,{
                'type':'friend_request_operations',
                'message':message
            }
        )

    async def friend_request_operations(self,event):
        content = event['content']
        print("its me mathi ko content ",content)
        await self.send(text_data=content)


class FriendRequestsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.me = self.scope['user']
        other_username = self.scope['url_route']['kwargs']['username']
        self.other_user = await sync_to_async(CustomUser.objects.get)(username=other_username)
        if self.me != self.other_user:
            self.thread_obj = await sync_to_async(FriendRequestThread.objects.get_or_create_personal_thread)(self.me,self.other_user)
            self.room_name = self.thread_obj.id
            self.room_group_name = 'ui_update_%s' % self.room_name
            print("friendrequest consumer room",self.room_group_name)
            await sync_to_async(self.thread_obj.connect)(self.me)
        else:
            self.room_group_name = 'ui_update_%s' % self.me.id
        #join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print("FriendRequest consumer")
    async def disconnect(self, close_code):
        try:
            await sync_to_async(self.thread_obj.disconnect)(self.me)
        except:
            print("there is no thread object")
            print(self.room_group_name,"yo disconnect wala room group")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self,text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        await self.channel_layer.group_send(
            self.room_group_name,{
                'type':"my_req_update",
                'message':message
            }
        )

    async def my_request_ui_update(self,event):
        content = event['content']
        print("its me ui content",content)
        await self.send(text_data=content)
