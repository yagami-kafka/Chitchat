from channels.generic.websocket import AsyncJsonWebsocketConsumer
class IndividualConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        print("individual consumer connect: " +str(self.scope['user']))
        self.me = self.scope.get('user')
        await self.accept()
        self.room_id = self.scope['url_route']['kwargs']['uid']
        self.room_group_name = f'threadlist_update_{self.room_id}'
        print("threadlist update is ",self.room_group_name)

        await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
    
    async def status_update(self,event):
        content = event['content']
        print("its me thread event",content)
        await self.send_json({
            "thread_details":content,
        })

    async def disconnect(self, close_code):
        me = self.scope['user']
        if self.room_group_name and self.channel_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )