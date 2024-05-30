from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.serializers import serialize
from django.http.response import JsonResponse
from django.utils import timezone
from django.db.models import F
import json
import asyncio
from accounts.utils import LazyCustomUserEncoder
from accounts.models import CustomUser
from core.exceptions import ClientError
from .utils import (CHAT_NAME_CHANGED, CHAT_PHOTO_CHANGED, DEFAULT_PAGE_SIZE, MSG_TYPE_ADDED, MSG_TYPE_NORMAL, MSG_TYPE_REMOVED, 
                    LazyGroupThreadMessageEncodeer, timestamp_encoder,LazyPrivateThreadMessageEncodeer, MEMBERS_ACTION)
from django.core.paginator import Paginator
from .DoubleDiffie import DiffieHellman
from channels.layers import get_channel_layer

from .models import (
    Keys, PrivateChatThread,PrivateChatMessage,GroupChatThread,GroupChatMessage
)
from friends.models import FriendList





def generate_test_keys(current_user,target_user):
    data = {}
    current_user = DiffieHellman()
    target_user = DiffieHellman()
    private_key_current_user,public_key_current_user = current_user.get_private_key(), current_user.generate_public_key()
    private_key_target_user,public_key_target_user = target_user.get_private_key(), target_user.generate_public_key()
    target_user_shared_key = target_user.generate_shared_key(public_key_current_user)
    current_user_shared_key = current_user.generate_shared_key(public_key_target_user)
    current_user_second_public_key = current_user.generate_second_public_key(current_user_shared_key)
    target_user_second_public_key = target_user.generate_second_public_key(target_user_shared_key)
    current_user_second_shared_key = current_user.generate_second_shared_key(target_user_second_public_key,current_user_shared_key)
    target_user_second_shared_key = target_user.generate_second_shared_key(current_user_second_public_key,target_user_shared_key)
    data['private_key_current_user'] = private_key_current_user
    data['public_key_current_user'] = public_key_current_user
    data['private_key_target_user'] = private_key_target_user
    data['public_key_current_user'] = public_key_target_user
    data['shared_key_target_user'] = target_user_second_shared_key
    data['shared_key_current_user'] = current_user_second_shared_key


    return json.dumps(data)
    

def generate_shared_keys(current_user,target_user):
    try:
        data = {}
        current_user_keys = Keys.objects.get(keys_owner = current_user)
        target_user_keys = Keys.objects.get(keys_owner = target_user)
        local_private_key = current_user_keys.private_key
        local_second_private_key = current_user_keys.second_private_key
        remote_second_private_key = target_user_keys.second_private_key
        remote_public_key = target_user_keys.public_key
        first_shared_key = DiffieHellman.generate_shared_key_static(local_private_key,remote_public_key)
        second_remote_public_key = DiffieHellman.generate_second_public_key_static(remote_second_private_key,first_shared_key)
        final_shared_key = DiffieHellman.generate_second_shared_key_static(local_second_private_key,second_remote_public_key,first_shared_key)

        data['final_shared_key'] = final_shared_key

        return json.dumps(data)
    except:
        raise ClientError(204,"Invalid public key")
        
class PrivateChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        await self.accept()
        self.room_name = f'private_thread_{user.id}'
        self.me = self.scope.get('user')
        print("yo me",self.me)
        self.other_username = self.scope['url_route']['kwargs']['friendId']
        print("yo other user",self.other_username)
        self.other_user = await sync_to_async(CustomUser.objects.get)(id= self.other_username)
        self.private_thread = await sync_to_async(PrivateChatThread.objects.create_room_if_none)(self.me, self.other_user)
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name,
        )
    # async def connect(self):
    #     print("private chat consumer connect: " +str(self.scope['user']))
    #     self.me = self.scope.get('user')
    #     await self.accept()
    #     self.other_username = self.scope['url_route']['kwargs']['friendId']
    #     print("yo other user",self.other_username)
    #     self.other_user = await sync_to_async(CustomUser.objects.get)(id= self.other_username)
    #     self.private_thread = await sync_to_async(PrivateChatThread.objects.create_room_if_none)(self.me, self.other_user)
    #     self.room_name = f'private_chat_{self.private_thread.id}'
    #     print("private chat thread is ",self.room_name)

    #     await sync_to_async(self.private_thread.connect)(self.me)

    #     print("added myself")

    #     await self.channel_layer.group_add(
    #         self.room_name,
    #         self.channel_name
    #     )
        

    #     if self.me.is_authenticated:
    #         await update_user_incr(self.me)

    async def receive_json(self, content, **kwargs):
        command = content.get("command",None)
        print("yo command ho ",command)
        try:
            if command == "join":
                t = await get_thread_or_error(self.private_thread.id,self.me)
                shared_key = await sync_to_async(generate_shared_keys)(self.scope['user'],self.other_user)
                my_keys = json.loads(shared_key)
                test_shared_keys = await sync_to_async(generate_test_keys)(self.scope['user'],self.other_user)
                test_shared_keys = json.loads(test_shared_keys)
                await self.channel_layer.group_send(
                        self.room_name,
                        {
                            "type": "websocket_join",
                            "join":str(self.private_thread.id),
                            "thread_type":"private_thread",
                            "my_keys":my_keys,
                            "shared_key_target_user":test_shared_keys['shared_key_target_user'],
                            "shared_key_current_user":test_shared_keys['shared_key_current_user'],  
                        }
                    )

            
            #when someone message to the chat 

            elif command == "private_chat":
                message = content.get("message")
                if len(message.lstrip()) == 0:
                    raise ClientError(422,"You can't send an empty message.")
                message_type = content['message_type']
                sent_by_id = content['sent_by']
                send_to_id = content['send_to']
                sent_by_user = await self.get_user_object(sent_by_id)
                send_to_user = await self.get_user_object(send_to_id)

                if not sent_by_user:
                    print("Error:: sent by user is incorrect")
                if not send_to_user:
                    print("Error:: send to user is incorrect")
                other_user_chat_room = f'private_thread_{send_to_id}'
                print("yo message",message)

                self.newmsg = await sync_to_async(PrivateChatMessage.objects.create)(
                chat_thread = self.private_thread,
                sender = self.scope['user'],
                message_type = message_type,
                )

                print("room name",self.room_name)
                await self.channel_layer.group_send(
                    self.room_name,{
                        "type": "websocket_message",
                        "text": message,
                        "id": self.newmsg.id,
                        "username": self.newmsg.sender.username,
                        "first_name":self.newmsg.sender.first_name,
                        "last_name":self.newmsg.sender.last_name,
                        "profile_image": self.newmsg.sender.profile_image.url,
                        "user_id": self.newmsg.sender.id,
                        "status": self.newmsg.sender.status,
                        "timestamp": timezone.localtime(self.newmsg.timestamp),
                        "command": command,
                        "send_to":send_to_id,
                        "sent_by":sent_by_id,
                        "thread_id":self.private_thread.id,
                    }
                    
                )
                await self.channel_layer.group_send(
                    other_user_chat_room,{
                        "type": "websocket_message",
                        "text": message,
                        "id": self.newmsg.id,
                        "username": self.newmsg.sender.username,
                        "first_name":self.newmsg.sender.first_name,
                        "last_name":self.newmsg.sender.last_name,
                        "profile_image": self.newmsg.sender.profile_image.url,
                        "user_id": self.newmsg.sender.id,
                        "status": self.newmsg.sender.status,
                        "timestamp": timezone.localtime(self.newmsg.timestamp),
                        "command": command,
                        "send_to":send_to_id,
                        "sent_by":sent_by_id, 
                        "thread_id":self.private_thread.id,
                    }
                    
                )

            elif command == "request_messages_data":
                await self.display_progress_bar(True)
                thread = await get_thread_or_error(self.private_thread.id,self.me)
                data = await get_thread_messages_data(thread,content['page_number'])
                if data!=None:
                    data = json.loads(data)
                    await self.broadcast_messages_data(data['messages_metadata'],data['new_page_number'],content['firstAttempt'])
                else:
                    raise ClientError(204,"Something went wrong while trying to fetch messages metadata.")

                await self.display_progress_bar(False)

            elif command == 'idb_broadcast':
                other_user_chat_room = f'private_thread_{self.other_user.id}'
                await self.channel_layer.group_send(
                    other_user_chat_room,
                    {
                        "type": "websocket_idbBroadcast",
                        "command":command,
                        "user_id":self.me.id,
                        "username":self.me.username,
                        "idb_message":content['idb_msg'],
                        "pvt_id":self.private_thread.id,
                    }
                )

            elif command == 'get_user_info':
                await self.display_progress_bar(True)
                thread = await get_thread_or_error(self.private_thread.id,self.scope['user'])
                print("user info ko thread",thread)
                data =await sync_to_async(get_user_info)(thread,self.scope['user'])
                
                if data!=None:
                    data = json.loads(data)
                    await self.broadcast_userinfo(data['user_info'])
                    # await self.channel_layer.group_send(
                    #     self.room_name,
                    #     {
                    #         "type": "websocket_userinfo",
                    #         "user_info": data['user_info'],
                    #         "command": command,
                    #     }
                    # )
                else:
                    raise ClientError(204,"Something went wrong while trying to fetch your contact's information.")
                await self.display_progress_bar(False)
            if command == "is_typing":
                sent_by_id = content['sent_by']
                send_to_id = content['send_to']
                sent_by_user = await self.get_user_object(sent_by_id)
                send_to_user = await self.get_user_object(send_to_id)
                if not sent_by_user:
                    print("Error:: sent by user is incorrect")
                if not send_to_user:
                    print("Error:: send to user is incorrect")
                other_user_chat_room = f'private_thread_{send_to_id}'
                await self.channel_layer.group_send(
                    self.room_name,
                    {
                        "type": "websocket_typing",
                        "text": f'{self.me.first_name} is typing',
                        "command": command,
                        "sent_by": sent_by_id,
                        "send_to": send_to_id,
                    }
                )
        except ClientError as e:
            await self.display_progress_bar(False)
            await self.handle_client_error(e)
    
    async def websocket_join(self,event):
        await self.send_json({
            'joining_room': str(self.private_thread.id),
            'thread_type': event['thread_type'],
            'shared_key_target_user':event['shared_key_target_user'],
            'shared_key_current_user':event['shared_key_current_user'],      
            'my_keys':event['my_keys'],
        })

    async def websocket_message(self,event):
        t = event['timestamp']
        timestamp = timestamp_encoder(t)
        await self.send_json(({
            'msg_id': event['id'],
            'message_content': event['text'],
            'command': event['command'],
            'status':event['status'],
            'natural_timestamp': timestamp,
            'username': event['username'],
            'first_name':event['first_name'],
            'last_name':event['last_name'],
            'profile_image': event['profile_image'],
            'user_id': event['user_id'],
            'send_to': event['send_to'],
            'sent_by':event['sent_by'],
            'private_thread_id':event['thread_id'],
        }))
        
    async def websocket_typing(self, event):
        await self.send_json((
            {
                'text': event['text'],
                'command': event['command'],
                'send_to': event['send_to'],
                'sent_by': event['sent_by'],
                'display_typing': True,
            }
        ))
    async def websocket_idbBroadcast(self, event):
        await self.send_json((
            {
                'idb_message': event['idb_message'],
                'command': event['command'],
                'user_id': event['user_id'],
                'username':event['username'],
                'pvt_id':event['pvt_id'],
            }
        ))    
    

    async def broadcast_messages_data(self,messsages_metadata,new_page_number,firstAttempt):
        print("Private thread: broadcasting messages metadata")
        await self.send_json(
            {   
                "messages_response": "messages_response",
                "messages_metadata": messsages_metadata,
                "new_page_number": new_page_number,
                "firstAttempt":firstAttempt,
            },
        )

    async def broadcast_userinfo(self,user_info):
        await self.send_json(
            {
                'user_info': json.dumps(user_info),
                'private_thread_id':self.private_thread.id,
            },
        )

    async def disconnect(self, close_code):
        me = self.scope['user']
        print("disconnect huda ko me",me)
        await sync_to_async(self.private_thread.disconnect)(me)
        await update_user_decr(me)
        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "chat_leave",
                "thread_id": self.private_thread.id,
                "username":me.username,
                "profile_image": me.profile_image.url,
                "user_id": me.id,
                "status": me.status,
            }
        )

        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name,
        )

    async def chat_leave(self,event):
        print("Chat consumer: chat_leave")
        if event['username']:
            await self.send_json(
                {
                "thread_id": event['thread_id'],
                "username":event['username'],
                "profile_image": event['profile_image'],
                "user_id": event['user_id'],
                "status": event['status'],
                }
            )

    async def display_progress_bar(self,is_displayed):
        print("DIsplay progress bar",is_displayed)
        await self.send_json(
            {
                "display_progress_bar":is_displayed,
            }
        )

    async def handle_client_error(self,e):
        errorData = {}
        errorData['error'] = e.code
        if e.message:
            errorData['message'] = e.message
            await self.send_json(errorData)
        return
    @database_sync_to_async
    def get_user_object(self,user_id):
        qs = CustomUser.objects.filter(id=user_id)
        if qs.exists():
            obj = qs.first()
        else:
            obj = None
        return obj
@database_sync_to_async
def get_thread_or_error(thread_id, user):
    try:
        thread = PrivateChatThread.objects.get(pk = thread_id)
    except PrivateChatThread.DoesNotExist:
        raise ClientError("THREAD_INVALID", "Invalid chat thread.")
    if user!=thread.first_user and user != thread.second_user:
        raise ClientError("ACCESS_DENIED", "You don't have permissiion to join this chat.")
    friend_list = FriendList.objects.get(user = user).friends.all()
    if not thread.first_user in friend_list:
        if not thread.second_user in friend_list:
            raise ClientError("ACCESS_DENIED", "You must be friends to chat.")
    return thread


def get_user_info(thread,user):
    try:
        other_user = thread.first_user
        if other_user == user:
            other_user = thread.second_user

        data = {}
        user_detail = LazyCustomUserEncoder()
        data['user_info'] = user_detail.get_dump_object(other_user)
        return json.dumps(data)
    except ClientError as e:
        raise ClientError("DATA_ERROR"," Unable to get the user information.")
    return None

@database_sync_to_async
def get_connected_users(private_thread):
    try:
        connected_users = private_thread.connected_users.all()
        print("connected users",connected_users)
        connected_users_id = [ f.id for f in connected_users]
        print(connected_users_id)
    except Exception as e:
        print(e)
    return connected_users_id


@database_sync_to_async
def get_thread_messages_data(thread,page_number):
    try:
        message_query = PrivateChatMessage.objects.by_private_thread(thread)
        paginator_obj = Paginator(message_query,DEFAULT_PAGE_SIZE)
        data = {}
        new_page_number = int(page_number)
        if new_page_number <= paginator_obj.num_pages:
            new_page_number = new_page_number + 1 
            message_detail = LazyPrivateThreadMessageEncodeer()
            data['messages_metadata'] = message_detail.serialize(paginator_obj.page(page_number).object_list)
        else:
            data["messages_metadata"] = "None"
        data['new_page_number'] = new_page_number
        return json.dumps(data)
    except Exception as e:
        print("SOMETHING WENT WRONG",e)
    return None



@database_sync_to_async
def update_user_incr(user):
    CustomUser.objects.filter(pk = user.pk).update(status = F('status')+1)

@database_sync_to_async
def update_user_decr(user):
    print("user ko decrement",user)
    CustomUser.objects.filter(pk = user.pk).update(status = F('status')-1)



class GroupChatConsumer(AsyncJsonWebsocketConsumer):
    msgType = [CHAT_NAME_CHANGED, CHAT_PHOTO_CHANGED, MSG_TYPE_ADDED, MSG_TYPE_NORMAL, MSG_TYPE_REMOVED]

    async def connect(self):
        print("group chat consumer connect: " +str(self.scope['user']))
        if self.scope['user'].is_anonymous:
            await self.close()
        self.me = self.scope.get('user')
        await self.accept()
        self.room_id = self.scope['url_route']['kwargs']['groupThreadId']
        self.group_chat_thread = await sync_to_async(GroupChatThread.objects.get)(id= self.room_id)
        self.room_group_name = f'group_chat_{self.room_id}'
        print("group chat thread is ",self.room_group_name)



        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        

    async def receive_json(self, content, **kwargs):
        command = content.get("command",None)
        requested_by = content.get("requested_by")
        print("yo command ho ",command)
        try:
            if command == "join":
                print("requested by ",requested_by)

                await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "websocket_join",
                            "join":str(self.room_id),
                            "thread_type":"group_thread",
                            "requested_by":requested_by,
                        }
                    )



            elif command == "group_chat":
                thread = await get_group_thread_or_error(self.group_chat_thread.id,self.scope['user'])
                message = content.get("message")
                message_type = content['message_type']
                print("yo message",message)
                self.newmsg = await sync_to_async(GroupChatMessage.objects.create)(
                gc_thread = self.group_chat_thread,
                sender = self.me,
                content = message,
                message_type = message_type,
                )

                print("room name",self.room_group_name)
                await self.channel_layer.group_send(
                    self.room_group_name,{
                        "type": "websocket_message",
                        "text": message,
                        "id": self.newmsg.id,
                        "username": self.newmsg.sender.username,
                        "first_name":self.newmsg.sender.first_name,
                        "last_name":self.newmsg.sender.last_name,
                        "profile_image": self.newmsg.sender.profile_image.url,
                        "user_id": self.newmsg.sender.id,
                        "status": self.newmsg.sender.status,
                        "timestamp": timezone.localtime(self.newmsg.timestamp),
                        "command": command  
                    }
                    
                )

            elif command == "request_group_messages_data":
                await self.display_progress_bar(True)
                thread = await get_group_thread_or_error(self.group_chat_thread.id,self.scope['user'])
                data = await get_group_thread_messages_data(thread,content['page_number'])
                if data!=None:
                    data = json.loads(data)
                    await self.broadcast_group_messages_data(data['messages_metadata'],data['new_page_number'],content['firstAttempt'])
                else:
                    raise ClientError(204,"Something went wrong while trying to fetch messages metadata.")

                await self.display_progress_bar(False)

            elif command == 'get_group_chat_info':
                await self.display_progress_bar(True)
                thread = await get_group_thread_or_error(self.group_chat_thread.id,self.scope['user'])
                print("groupchat info ko thread",thread)
                data =await sync_to_async(get_group_chat_info)(thread)
                
                if data!=None:
                    data = json.loads(data)
                    await self.broadcast_group_chat_info(data['group_chat_info'])
                    # await self.channel_layer.group_send(
                    #     self.room_name,
                    #     {
                    #         "type": "websocket_userinfo",
                    #         "user_info": data['user_info'],
                    #         "command": command,
                    #     }
                    # )
                else:
                    raise ClientError(204,"Something went wrong while trying to fetch your contact's information.")
                await self.display_progress_bar(False)
            if command == "is_typing":
                thread = await get_group_thread_or_error(self.group_chat_thread.id,self.scope['user'])
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "websocket_typing",
                        "text": f'{self.me.first_name} is typing',
                        "command": command,
                        "user": self.me.first_name,
                    }
                )
            if command == 'leave_group_chat':
                return await self.close()
        except ClientError as e:
            await self.display_progress_bar(False)
            await self.handle_client_error(e)
    
    async def websocket_join(self,event):
        room_id = event['join']
        await self.send_json({
            'joining_group_chat': str(room_id),
            'thread_type': event['thread_type'],
            "requested_by":event['requested_by'],

        })

    async def websocket_message(self,event):
        print("instant message broadcast hudai")
        t = event['timestamp']
        timestamp = timestamp_encoder(t)
        await self.send_json(({
            'msg_type':MSG_TYPE_NORMAL,
            'msg_id': event['id'],
            'message_content': event['text'],
            'command': event['command'],
            'status':event['status'],
            'natural_timestamp': timestamp,
            'username': event['username'],
            'first_name':event['first_name'],
            'last_name':event['last_name'],
            'profile_image': event['profile_image'],
            'user_id': event['user_id'],
            'group_thread_id':self.room_id,
            'msgTypeList':self.msgType,
        }))
        
    async def websocket_typing(self, event):
        await self.send_json((
            {
                'text': event['text'],
                'command': event['command'],
                'user': event['user'],
                'grp_display_typing' : True,
            }
        ))
    

    async def broadcast_group_messages_data(self,messsages_metadata,new_page_number,firstAttempt):
        print("Group chat thread: broadcasting messages metadata")
        await self.send_json(
            {   
                "messages_response": "messages_response",
                "messages_metadata": messsages_metadata,
                "new_page_number": new_page_number,
                "firstAttempt":firstAttempt,
            },
        )

    async def broadcast_group_chat_info(self,group_chat_info):
        await self.send_json(
            {
                'group_chat_info': json.dumps(group_chat_info),
                'group_thread_id':self.room_id,
                
            },
        )

    async def disconnect(self, close_code):
        me = self.scope['user']
        print("disconnect huda ko group chat ko me",me)
        # await self.channel_layer.group_send(
        #     self.room_group_name,
        #     {
        #         "type": "chat_leave",
        #         "thread_id": self.group_chat_thread.id,
        #         "username":me.username,
        #         "profile_image": me.profile_image.url,
        #         "user_id": me.id,
        #         "status": me.status,
        #     }
        # )
        if self.room_group_name and self.channel_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def chat_name_changed(self,event):
        print("chat name event",event)
        content = json.loads(event['content'])
        await self.send_json(
            {
                "msg_type": CHAT_NAME_CHANGED,
                "command":"group_chat",
                "thread_id": self.room_id,
                "username":content['username'],
                "new_chat_name":content['new_gc_name'],
                "user_id":content['user_id'],
                "msgTypeList": self.msgType,
            }
        )
    async def chat_photo_changed(self,event):
        content = json.loads(event['content'])
        await self.send_json(
            {
                "msg_type": CHAT_PHOTO_CHANGED,
                "command":"group_chat",
                "thread_id": self.room_id,
                "username":content['username'],
                "new_chat_photo":content['new_gc_photo'],
                "user_id":content['user_id'],
                "msgTypeList": self.msgType,
            }
        )

    async def member_added(self,event):
        print("New member added")
        content = json.loads(event['content'])
        gc_thread = await sync_to_async(GroupChatThread.objects.get)(id = content['thread_id'])
        data = await sync_to_async(get_group_chat_info)(gc_thread)
        await self.send_json(
                {
                    "msg_type": MSG_TYPE_ADDED,
                    "command": "group_chat",
                    "action":content['action'],
                    "added_members":content['added_members'],
                    "members_info": json.loads(data)['group_chat_info'],
                    "msgTypeList":self.msgType,
                    "actionList":MEMBERS_ACTION,
                }
            )
    async def member_removed(self,event):
        content = json.loads(event['content'])
        gc_thread =await sync_to_async( GroupChatThread.objects.get)(id = content['gc_thread_id'])
        removee = content['removee']
        data  = await sync_to_async(get_group_chat_info)(gc_thread)
        await self.send_json(
                {
                    "msg_type": MSG_TYPE_REMOVED,
                    "command": "group_chat",
                    "members_info": json.loads(data)['group_chat_info'],
                    "action":content['action'],
                    "removee":removee,
                    "msgTypeList": self.msgType,
                    "actionList":MEMBERS_ACTION,
                }
            )
        print("self channel name ",self.scope['user'])
    async def group_chat_leave(self,event):
        print("Chat consumer: chat_leave")
        content = json.loads(event['content'])
        gc_thread = await sync_to_async(GroupChatThread.objects.get)(id = content['gc_thread_id'])
        data = await sync_to_async(get_group_chat_info)(gc_thread)
        await self.send_json(
                {
                "msg_type": MSG_TYPE_REMOVED,
                "command":"group_chat",
                "members_info": json.loads(data)['group_chat_info'],
                "action":content['action'],
                "left_user":content['left_user'],
                "msgTypeList": self.msgType,
                "actionList":MEMBERS_ACTION,
                }
            )


    async def display_progress_bar(self,is_displayed):
        print("DIsplay progress bar",is_displayed)
        await self.send_json(
            {
                "display_progress_bar":is_displayed,
            }
        )
    # async def display_is_typing(self,is_displayed):
    #     await self.send_json(
    #         {
    #             "display_is_typing":is_displayed,

    #         }
    #     )

    async def handle_client_error(self,e):
        errorData = {}
        errorData['error'] = e.code
        if e.message:
            errorData['message'] = e.message
            await self.send_json(errorData)
        return

@database_sync_to_async
def get_group_thread_or_error(thread_id,user):
    try:
        thread = GroupChatThread.objects.get(pk = thread_id)
        thread_members = thread.user_set.all()
    except GroupChatThread.DoesNotExist:
        raise ClientError("THREAD_INVALID", "Invalid chat thread.")
    if not user in thread_members:
        raise ClientError("ACCESS_DENIED", "You don't have permissiion to join this chat.")
    return thread


def get_group_chat_info(thread):
    try:
        data = {}
        print(thread.id)
        member_detail = LazyCustomUserEncoder()
        thread_members = thread.user_set.all()
        print(thread_members)
        member_details_list = []
        for m in thread_members:
            m_detail = member_detail.get_dump_object(m)
            member_details_list.append(m_detail)
        
        data['group_chat_info'] = {
                                    "thread_id":thread.id,
                                    "group_name":thread.group_name,
                                    "image":thread.image.url,
                                    "admin_id":thread.admin.id,
                                    "admin_username":thread.admin.username,
                                    "members":member_details_list,
                                    "group_description":thread.group_description,
                                    }
        return json.dumps(data)
    except ClientError as e:
        raise ClientError("DATA_ERROR"," Unable to get the group chat information.")
    return None

@database_sync_to_async
def get_group_thread_messages_data(thread,page_number):
    try:
        message_query = GroupChatMessage.objects.by_gc_thread(thread)
        paginator_obj = Paginator(message_query,DEFAULT_PAGE_SIZE)
        data = {}
        new_page_number = int(page_number)
        if new_page_number <= paginator_obj.num_pages:
            new_page_number = new_page_number + 1 
            message_detail = LazyGroupThreadMessageEncodeer()
            data['messages_metadata'] = message_detail.serialize(paginator_obj.page(page_number).object_list)
        else:
            data["messages_metadata"] = "None"
        data['new_page_number'] = new_page_number
        return json.dumps(data)
    except Exception as e:
        print("SOMETHING WENT WRONG",e)
    return None



class ThreadListUpdateConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        print("thread update connect: " +str(self.scope['user']))
        self.me = self.scope.get('user')
        await self.accept()
        self.room_id = self.scope['url_route']['kwargs']['uid']
        self.room_group_name = f'threadlist_update_{self.room_id}'
        print("threadlist update is ",self.room_group_name)

        await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
    
    async def thread_update(self,event):
        print("Method is being called")
        content = event['content']
        
        print("its me thread event",content)
        await self.send_json({
            "thread_details":content,
            
        })

    async def members_ui_update(self,event):
        content = event['content']
        # gc_thread = await sync_to_async(GroupChatThread.objects.get)(id = content['gc_thread_id'])
        # print("gc thread members",gc_thread)
        # group_info = await sync_to_async(get_group_chat_info)(gc_thread)
        await self.send_json({
            "user_action":content,
        })

    async def disconnect(self, close_code):
        me = self.scope['user']
        if self.room_group_name and self.channel_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )



