
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.serializers import serialize
from django.http.response import JsonResponse
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import Value as V
from django.db.models.functions import Concat
from datetime import datetime
from accounts.models import CustomUser
from core.DoubleDiffie import DiffieHellman
from core.exceptions import ClientError
from friends.models import FriendList
from .forms import GroupChatCreationForm
from .models import GroupChatThread, Keys, PrivateChatMessage, PrivateChatThread
from itertools import chain
from .serializers import PrivateChatThreadSerializer, GroupChatThreadSerializer, UserSerializer
from rest_framework.response import Response
from rest_framework import viewsets
from operator import attrgetter
from .consumers import generate_shared_keys
from ChatApp import settings,broadcast
from ChatApp.query_debugger import query_debugger
import pytz
from .models import GroupJoinedDate
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from .utils import MEMBER_ADDED,MEMBER_REMOVED,GROUP_LEFT

# Create your views here.

DEBUG = False

@login_required
def chat_section(request):
    return render(request,'core/chat_section.html')


@login_required
def chat_thread_view(request,*args,**kwargs):
    current_user = request.user
    group = None
    logged_user = CustomUser.objects.values(
        'id',
        'first_name',
        'last_name',
        'username',
        'profile_image',
    ).get(id = current_user.id)
    thread_id = request.GET.get('t_id')
    group_t_id = request.GET.get('gt_id')
    context = {}

    if group_t_id:
        try:
            group_thread = get_group_thread_or_error(group_t_id,current_user)
            context['gt_id'] = group_thread.id
        except ClientError as e:
            context['invalid_gt_id'] = e.message
    context['current_user'] = logged_user
    if thread_id:
        context['t_id'] = thread_id
        # try:
        #     private_thread = get_thread_or_error(thread_id,current_user)
        #     print(private_thread.first_user,private_thread.second_user)
        #     context['private_thread'] = private_thread
        # except ClientError as e:
        #     print(e.message)
        #     context['response'] = e.message
        #     return JsonResponse(context['response'],safe=False)

        # context['private_thread_json'] = PrivateChatThreadSerializer(private_thread).data
    threads1 = PrivateChatThread.objects.filter(first_user = current_user, is_active = True)
    threads2 = PrivateChatThread.objects.filter(second_user = current_user, is_active = True)
    group_ids = current_user.groups.values_list('id')
    group_threads = GroupChatThread.objects.filter(id__in = group_ids)
    threads = sorted(chain(threads1, threads2,group_threads),key = attrgetter('updated_at'),reverse = True)
    thread_users_id = []
    for thread in threads:
        if hasattr(thread,'first_user') or hasattr(thread,'second_user'):
            if thread.first_user == current_user:
                friend = thread.second_user
            else:
                friend = thread.first_user
            thread_users_id.append(friend.id)
            friend_list = FriendList.objects.get(user = current_user)
            if not friend_list.is_mutual_friend(friend):
                private_chat = PrivateChatThread.objects.create_room_if_none(current_user,friend)
                private_chat.is_active = False
                private_chat.save()
        else:
            group = thread
    keys = []
    for id in thread_users_id:
        target_user = CustomUser.objects.get(pk = id)
        sh_key = generate_shared_keys(current_user,target_user)
        sh_key = json.loads(sh_key)
        keys.append(sh_key['final_shared_key'])
    context['keys'] = keys
    context['chat_threads'] = threads
    context['thread_id'] = thread_id
    return render(request,"core/index.html",context)

@login_required
def test_room_view(request,*args,**kwargs):
    room_id = request.GET.get("room_id")
    user = request.user
    context = {}
    context['m_and_f'] = get_recent_chatroom_messages(user)
    if room_id:
        context['room_id'] = room_id
    context['debug'] = DEBUG
    context['debug_mode'] = settings.DEBUG
    return render(request,"core/test_demo.html",context)

def get_recent_chatroom_messages(user):
    rooms1 = PrivateChatThread.objects.filter(first_user = user, is_active = True)
    rooms2 = PrivateChatThread.objects.filter(second_user = user, is_active = True)
    rooms = list(chain(rooms1,rooms2))

    m_and_f = []
    for room in rooms:
        if room.first_user == user:
            friend = room.second_user
        else:
            friend = room.first_user

        friend_list = FriendList.objects.get(user= user)
        if not friend_list.is_mutual_friend(friend):
            chat = PrivateChatThread.objects.create_room_if_none(user,friend)
            chat.is_active = False
            chat.save()
        else:
            try:
                message = PrivateChatMessage.objects.filter(chat_thread = room, sender= friend).latest("timestamp")
            except PrivateChatMessage.DoesNotExist:
                today = datetime(
                    year=1950,
                    month = 1,
                    day=1,
                    hour=1,
                    minute=1,
                    second=1,
                    tzinfo=pytz.UTC
                )
                message = PrivateChatMessage(
                    sender = friend,
                    chat_thread = room,
                    timestamp = today,
                    message_type = "text",
                    message_content = "",
                )
            m_and_f.append({
                'message':message,
                'friend':friend,
            })
    return sorted(m_and_f, key=lambda x: x['message'].timestamp, reverse=True)



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


    
@login_required
def create_or_return_private_chat(request, *args,**kwargs):
    first_user = request.user
    data = {}
    if request.is_ajax() and request.method == "POST":
        second_user_id = request.POST.get("second_user_id")
        try:
            second_user = CustomUser.objects.get(pk = second_user_id)
            private_thread = PrivateChatThread.objects.create_room_if_none(first_user,second_user)
            try:
                pvt_thread = get_thread_or_error(private_thread.id,first_user)
                data['response'] = "Successfully got the chat."
                data['private_thread_id'] = pvt_thread.id
            except ClientError as e:
                data['response'] = e.message

        except CustomUser.DoesNotExist:
            data['response'] = "Unable to start a chat with that user."
    else:
        return HttpResponse("Sorry something went wrong")
    return JsonResponse(data)


@login_required
def add_member_search(request,*args, **kwargs):
    if request.is_ajax() and request.method =='POST':
        current_user_id = request.user.id
        thread_id = None

        search_query = request.POST.get('search_query')
        thread_id = request.POST.get('thread_id')
        print("checking thread id",thread_id)
        if not search_query:
            print("Empty inserted")
            result = "No user found ..."
        else:
            print("search query",search_query)
            if thread_id:
                gc = GroupChatThread.objects.get(id = thread_id)
                gc_members = gc.user_set.all()
                gc_members_id = gc_members.values_list('id')
                print(gc_members_id)
                user_obj = CustomUser.objects.annotate(
                    full_name=Concat('first_name', V(' '), 'last_name')
                ).filter(Q(full_name__icontains = search_query) |
                    Q(first_name__icontains = search_query)
                    | Q(last_name__icontains = search_query) | Q(username__icontains = search_query)).exclude(id__in = gc_members_id)
            else:
                user_obj = CustomUser.objects.annotate(
                    full_name=Concat('first_name', V(' '), 'last_name')
                ).filter(Q(full_name__icontains = search_query) |
                    Q(first_name__icontains = search_query)
                    | Q(last_name__icontains = search_query) | Q(username__icontains = search_query)).exclude(id = current_user_id)
            if len(user_obj) >0 and len(search_query) >0:
                data = []
                for obj in user_obj:
                    item = {
                        'pk': obj.pk,
                        'first_name': obj.first_name,
                        'last_name':obj.last_name,
                        'username':obj.username,
                        'profile_image':str(obj.profile_image.url),
                    }
                    data.append(item)
                result = data
            else:
                result = "No user found ... "
        return JsonResponse({
            'data':result
        })
    else:
        return HttpResponse("Bad request ",504)

def get_group_members(group_id=None, group_obj=None, user=None):
    
    if group_id:
        groupchat = GroupChatThread.objects.get(id=id)
    else:
        groupchat = group_obj

    current_members= []
    for member in groupchat.user_set.values_list('username', flat=True):
        if member != user:
            current_members.append(member.title())
    current_members.append('You')
    return ', '.join(current_members)



class ThreadViewSet(viewsets.ViewSet):
    def list(self,request):
        print("api got hit")
        param = request.GET.get('u_id')
        if param:
            current_user = CustomUser.objects.get(id = param)
        else:
            current_user = request.user
        group_ids = current_user.groups.values_list('id')
        assigned_groups = GroupChatThread.objects.filter(id__in = group_ids)
        pvt_threads1 = PrivateChatThread.objects.filter(first_user = current_user,is_active = True)
        pvt_threads2 = PrivateChatThread.objects.filter(second_user = current_user, is_active = True)
        combined_threads = list(chain(pvt_threads1,pvt_threads2))
        private_serializer = PrivateChatThreadSerializer(combined_threads,many = True)
        group_serializer = GroupChatThreadSerializer(assigned_groups,many = True)
        response = private_serializer.data + group_serializer.data
        my_threads_dict = {}
        threads = sorted(response,key=lambda x: x['updated_at'],reverse=True)
        my_threads_dict['chat_threads'] = threads
        return Response(my_threads_dict)

def get_group_thread_or_error(thread_id,user):
    try:
        thread = GroupChatThread.objects.get(pk = thread_id)
        thread_members = thread.user_set.all()
    except GroupChatThread.DoesNotExist:
        raise ClientError("THREAD_INVALID", "Invalid chat thread.")
    if not user in thread_members:
        raise ClientError("ACCESS_DENIED", "You don't have permissiion to join this chat.")
    return thread

@login_required
def create_group_chat(request,*args,**kwargs):
    form = GroupChatCreationForm(request.POST or None, request.FILES or None)
    if request.is_ajax() and request.method == "POST":    
        current_user = request.user
        data = {}
        members_list_id = form.data.get('members_list')
        members_list_id = members_list_id.split(',')
        members_list_id.append(current_user.id)
        try:
            users = CustomUser.objects.filter(id__in = members_list_id)
        except:
            return JsonResponse({"response":"Something went wrong. Please try again"})
        last_group = GroupChatThread.objects.all().last()
        g = Group.objects.all().last()
        if form.is_valid():
            group_name = form.cleaned_data.get('group_name')
            gc_thread = form.save(commit=False)
            gc_thread.admin = current_user
            if last_group:
                gc_thread.name = group_name+str(last_group.pk+1)
            else:
                gc_thread.name = group_name+'001'
            print(gc_thread.admin)
            gc_thread.save()
            print("naya thread ko id",gc_thread.id)
            this_group = Group.objects.get(id = gc_thread.id)
            gc_thread.add_members(this_group,users)
            records = [{"gc":gc_thread,"user":u} for u in users]
            GroupJoinedDate.objects.bulk_create([GroupJoinedDate(**values) for values in records])
            data['status'] = 'Created'
            #threadlist_update_
            #thread_update
            consumer_method_name = 'thread_update'
            channel_layer = get_channel_layer()
            for id in members_list_id:
                print("id of members",id)
                room_group_name = f'threadlist_update_{id}'
                data['thread_details'] = thread_details(id)
                print(room_group_name)
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        "type":consumer_method_name,
                        "content":data['thread_details'],
                    }
                )
            return JsonResponse(data)
        return JsonResponse("testing",safe=False)
    else:
        return HttpResponse("Not allowed")

def thread_details(u_id):
    current_user = CustomUser.objects.get(id = u_id)
    group_ids = current_user.groups.values_list('id')
    assigned_groups = GroupChatThread.objects.filter(id__in = group_ids)
    pvt_threads1 = PrivateChatThread.objects.filter(first_user = current_user,is_active = True)
    pvt_threads2 = PrivateChatThread.objects.filter(second_user = current_user, is_active = True)
    combined_threads = list(chain(pvt_threads1,pvt_threads2))
    private_serializer = PrivateChatThreadSerializer(combined_threads,many = True)
    group_serializer = GroupChatThreadSerializer(assigned_groups,many = True)
    response = private_serializer.data + group_serializer.data
    my_threads_dict = {}
    threads = sorted(response,key=lambda x: x['updated_at'],reverse=True)
    my_threads_dict['chat_threads'] = threads
    return my_threads_dict

@login_required
def update_group_chat_name(request,*args,**kwargs):
    if request.is_ajax() and request.method=="POST":
        data = {}
        change_group_name = request.POST.get("change_group_name")
        thread_id = request.POST.get("thread_id")
        print(change_group_name,thread_id)
        this_group_chat= GroupChatThread.objects.get(id = thread_id)
        this_group_chat.group_name = change_group_name
        this_group_chat.save()
        new_group_chat_name = this_group_chat.group_name
        room_group_name = f'group_chat_{thread_id}'
        consumer_method_name = 'chat_name_changed'
        print(new_group_chat_name)
        data['status'] = "changed"
        data['username'] = request.user.username
        data['user_id'] = request.user.id
        data['new_gc_name'] = new_group_chat_name
        broadcast.perform_broadcast(data,room_group_name,consumer_method_name)
        return JsonResponse(data)

@login_required
def update_group_chat_photo(request,*args,**kwargs):
    if request.is_ajax() and request.method=="POST":
        data = {}
        change_group_photo = request.FILES.get("change_group_photo")
        thread_id = request.POST.get("thread_id")
        this_group_chat= GroupChatThread.objects.get(id = thread_id)
        this_group_chat.image = change_group_photo
        this_group_chat.save()
        new_group_chat_photo = this_group_chat.image.url
        room_group_name = f'group_chat_{thread_id}'
        consumer_method_name = 'chat_photo_changed'
        data['username'] = request.user.username
        data['user_id'] = request.user.id
        data['status'] = "changed"
        data['new_gc_photo'] = new_group_chat_photo
        broadcast.perform_broadcast(data,room_group_name,consumer_method_name)
        return JsonResponse(data)

@login_required
def add_members_to_chat(request,*args,**kwargs):
    if request.method=="POST" and request.is_ajax():
        data = {}
        thread_id = request.POST.get("thread_id")
        members_list_id = request.POST.get('members_list')
        members_list_id = members_list_id.split(',')
        try:
            users = CustomUser.objects.filter(id__in = members_list_id)
            gc_thread = GroupChatThread.objects.get(pk = thread_id)
            this_group = Group.objects.get(id = gc_thread.id)
            gc_thread.add_members(this_group,users)
            records = [{"gc":gc_thread,"user":u} for u in users]
            GroupJoinedDate.objects.bulk_create([GroupJoinedDate(**values) for values in records])
            # joined_dates = GroupJoinedDate.objects.filter(gc = gc_thread,user__in = members_list_id).select_related('gc')
            # [{"user_id":d.user.id,"group_name":d.gc.group_name,"group_id":d.gc.group_id,"username":d.user.username,"joined_date":d.joined_date} for d in joined_dates]
            # print("joined_dates",joined_dates)
            consumer_method_name = 'thread_update'
            channel_layer = get_channel_layer()
            for id in members_list_id:
                room_group_name = f'threadlist_update_{id}'
                data['thread_details'] = thread_details(id)
                print(room_group_name)
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        "type":consumer_method_name,
                        "content":data['thread_details'],
                    }
                )
            data['action'] = MEMBER_ADDED
            serializer = UserSerializer(users,many = True)
            data['added_members'] = serializer.data
            data['thread_id'] = thread_id
            broadcast.perform_broadcast(data,f'group_chat_{thread_id}','member_added')
            return JsonResponse(data)
        except CustomUser.DoesNotExist:
            return JsonResponse({"response":"No such user exist."})       
    else:
        return HttpResponse("No you can't do such things")


@login_required
def remove_group_member(request,*args,**kwargs):
    if request.method =="POST" and request.is_ajax():    
        removee_id = int(request.POST.get("removee_id"))
        current_user = request.user
        group_id = int(request.POST.get("thread_id"))
        gc_thread = GroupChatThread.objects.get(pk = group_id)
        admin_id = gc_thread.admin.id
        print("admin id",admin_id)
        data = {}
        if current_user.id == admin_id:
            removee = CustomUser.objects.get(id = removee_id)
            if removee in gc_thread.user_set.all().exclude(id = current_user.id):
                print("present in group",removee)
                removee.grp_joined_user.filter(gc= gc_thread).delete()
                gc_thread.user_set.remove(removee)
                room_group_name = f'group_chat_{gc_thread.id}'
                consumer_method_name = 'member_removed'
                data['gc_thread_id'] = gc_thread.id
                data['removee'] = {'first_name':removee.first_name,'last_name':removee.last_name,'username':removee.username}
                data['action'] = MEMBER_REMOVED
                broadcast.perform_broadcast(data,room_group_name,consumer_method_name)
                return JsonResponse({"response":"Member removed"})
            else:
                return JsonResponse({"response":"Invalid action"})
        else:
            print("Invalid action")
            return JsonResponse({"response":"Invalid action"})

@login_required
def leave_group(request,*args,**kwargs):
    if request.method =="POST" and request.is_ajax():    
        current_user = request.user
        group_id = int(request.POST.get("thread_id"))
        gc_thread = GroupChatThread.objects.get(pk = group_id)
        gc_admin = gc_thread.admin
        ordered_group_members = gc_thread.user_set.all().order_by('date_joined')
        group_members = gc_thread.user_set.all()
        print("ordered group_members",ordered_group_members)
        room_group_name = f'group_chat_{gc_thread.id}'
        consumer_method_name = 'group_chat_leave'
        data = {}
        if current_user in group_members:
            gc_thread.user_set.remove(current_user)
            current_user.grp_joined_user.filter(gc= gc_thread).delete()
            data['gc_thread_id'] = gc_thread.id
            data['action'] = GROUP_LEFT
            data['left_user'] = UserSerializer(current_user).data
            if current_user == gc_admin:
                new_admin = GroupJoinedDate.objects\
                    .filter(gc=gc_thread,user__in = group_members.exclude(id = current_user.id))\
                        .select_related('user').order_by('joined_date').first().user
                gc_thread.admin = new_admin
                gc_thread.save()
                print("new admin",new_admin)
                data['new_admin'] = UserSerializer(new_admin).data
                # return JsonResponse({"new admin":[new_admin.username,"group left"]})
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                    f'threadlist_update_{current_user.id}',
                    {
                        "type":'members_ui_update',
                        "content":'group_left',
                    }
                )
            members_list_id = [user.id for user in group_members]
            print("leave group chat ids list",members_list_id)
            for id in members_list_id:
                room_name = f'threadlist_update_{id}'
                data['thread_details'] = thread_details(id)
                print(room_group_name)
                async_to_sync(channel_layer.group_send)(
                    room_name,
                    {
                        "type":'thread_update',
                        "content":data['thread_details'],
                    }
                )
            broadcast.perform_broadcast(data,room_group_name,consumer_method_name)

            return JsonResponse({"response":"group left"})
        else:
            return JsonResponse({"response":"Invalid action"})
    else:
        return JsonResponse({"response":"Invalid action"})



@login_required
def gsk(request,*args,**kwargs):
    if request.method=="POST" and request.is_ajax():
        data = {}
        user_ids = request.POST.getlist('users_id[]')
        ks = []
        for id in user_ids:
            target_user = CustomUser.objects.get(pk = id)
            key = generate_shared_keys(request.user,target_user)
            key = json.loads(key)
            ks.append(key['final_shared_key'])
        data['ks'] = ks
        return JsonResponse(data)
    else:
        return HttpResponse("not allowed")

def generate_keys(request):
    data = {}
    dh = DiffieHellman()
    private_key,public_key,second_private_key= dh.get_private_key(), dh.generate_public_key(),dh.get_second_private_key()
    data['private_key'] = private_key
    data['second_private_key'] = second_private_key
    data['public_key'] = public_key
    return JsonResponse(data)

from asgiref.sync import sync_to_async
import aiohttp
import requests
import threading
import logging
@async_to_sync
async def test_api(request):
    # thread = threading.Thread(target=test_api_async, args=(request,))
    # thread.start()
    print("Thread has started")
    # return HttpResponse("Processing request in a separate thread")
    output = await test_api_async(request)
    print("OUTPUT ",output)
    return HttpResponse(output)
async def test_api_async(request):
    logging.info("TEst api got hit")
    r = requests.get('http://localhost:8000/chat/chat_thread_list')
    logging.info("RESPONSE",r.text())
    return HttpResponse(r.text())