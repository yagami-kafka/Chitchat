from django.http import response
from django.http.response import JsonResponse
from django.shortcuts import render
from django.http import HttpResponse
import json
from itertools import chain
from django.core import serializers
from ChatApp.broadcast import perform_broadcast
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser
from friends.models import FriendRequest,FriendList, FriendRequestThread
# Create your views here.

REQUEST_SUCCESS = "Friend request has been sent."
ERROR = "Something went wrong."
NO_USER_ID = "Unable to perform action. User id not available."
ALREADY_SENT = "You have already sent the request."
NOTHING_TO_CANCEL = "Nothing to cancel. Request doesnot exist."
REQUEST_CANCEL = "Friend request cancelled."
REQUEST_ACCEPTED = "Friend request accepted."
REQUEST_DECLINED = "Friend request declined."
NOT_YOUR_REQUEST = "This is not your request to perform action."
NO_REQUEST_TO_ACCEPT = "Nothing to accept. Request doesnot exist."
NO_REQUEST_TO_DECLINE = "Nothing to decline. Request doesnot exist."
FRIEND_REMOVED = "Friend removed successfully."


@login_required
def view_friend_list(request, *args, **kwargs):
    if request.is_ajax():
        data = {}
        current_user = request.user
        is_self = True
        user_id = kwargs.get('userId')
        print("user_id",user_id)
        if user_id:
            try:
                this_user = CustomUser.objects.get(pk = user_id)
                room_name_postfix = this_user.username
                print("this is this user",this_user)
            except CustomUser.DoesNotExist:
                return HttpResponse("User not available.")
            try:
                friend_list = FriendList.objects.get(user = this_user)
            except FriendList.DoesNotExist:
                return HttpResponse(f"Friend list not available")

            if current_user!=this_user:
                if not current_user in friend_list.friends.all():
                #     return HttpResponse(
                #         '<div class="d-flex flex-row flex-grow-1 justify-content-center align-items-center p-4"><p>You must be friends to see the friends of each other.</p></div>'
                # )
                    print("ta friend chainas")
                    data['friends'] = None
                    return JsonResponse(data)
                is_self = False
            friends = []
            current_user_friend_list = FriendList.objects.get(user = current_user)
            for friend in friend_list.friends.all():
                item = {
                    'id':friend.id,
                    'first_name':friend.first_name,
                    'last_name':friend.last_name,
                    'profile_image':friend.profile_image.url,
                    'username':friend.username,
                }
                friends.append((item, current_user_friend_list.is_mutual_friend(friend)))
            data['friends'] = friends
            data['is_self'] = is_self
            friendlist_view_method = 'friend_request_operations'
            btn_room_group_name = "friend_request_"+room_name_postfix
            perform_broadcast(data,btn_room_group_name,friendlist_view_method)
            return JsonResponse(data)
    else:
        return HttpResponse("Not found error 404")
            
            

    # else:
    #     return HttpResponse("404 not found.")
    


@login_required
def friend_requests(request, *args, **kwargs):
    data = {}
    current_user = request.user
    user_id = kwargs.get("userId")
    print("friend request view ko request herne "+str(user_id))
    print(current_user)
    user_account = CustomUser.objects.get(pk = user_id)
    room_name_postfix = user_account.username
    if user_account == current_user:
        friend_requests = FriendRequest.objects.filter(receiver = user_account, is_pending = True)
        sender_ids = friend_requests.values('sender_id')
        sender_qs = CustomUser.objects.filter(id__in = sender_ids).order_by('request_sender')
        data['sender'] = list(sender_qs.values(
            'username',
            'first_name',
            'last_name',
            'id',
            'profile_image',
            ))
        data['friend_requests'] = list(friend_requests.values('id','receiver','sender'))
        # temp_list = []
        # for row in friend_requests:
        #     temp_list.append({
        #         'id':row.id,
        #         'sender_uname':row.sender.username,
        #         'sender_fname':row.sender.first_name,
        #         'sender_lname':row.sender.last_name,
        #         'sender_image':row.sender.profile_image.url,
        #         'sender_id':row.sender.id,
        #         'receiver_uname':row.receiver.username,
        #         'receiver_id':row.receiver.id,
        #         'is_pending':row.is_pending,
        #         })
        friendrequest_view_method = 'friend_request_operations'
        btn_room_group_name = "friend_request_"+room_name_postfix
        perform_broadcast(data,btn_room_group_name,friendrequest_view_method)

        return JsonResponse(data)
    else:
        return HttpResponse("You can't see other person's requests.")
        
    
    # return JsonResponse(json.dumps(temp_list),safe=False)



@login_required
def send_request(request):
    current_user = request.user
    data = {}
    if request.is_ajax() and request.method == 'POST':
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            receiver = CustomUser.objects.get(pk = user_id)
            room_name_postfix = receiver.username
            thread_obj = FriendRequestThread.objects.get_or_create_personal_thread(current_user,receiver)
            print("this is send request check thread",thread_obj)
            data['thread_id'] = thread_obj.id
            try:
                friend_request_if_any = FriendRequest.objects.get(sender = current_user, receiver = receiver)
                if friend_request_if_any.is_pending:
                    data['result'] = ALREADY_SENT
                    return JsonResponse(data)
                friend_request_if_any.is_pending = True
                friend_request_if_any.save()
                data['result'] = REQUEST_SUCCESS

                # try:
                #     for req in friend_request_if_any:
                #         if req.is_pending:
                #             data['result'] = ALREADY_SENT
                #             print("feri")
                #             return JsonResponse(data)
                #             raise Exception("You already sent the request.")
                #     friend_request = FriendRequest(sender = current_user, receiver = receiver)
                #     print(friend_request)
                #     friend_request.save()
                #     data['result'] = REQUEST_SUCCESS
                # except Exception as e:
                #     data['result'] = str(e)
            except FriendRequest.DoesNotExist:
                friend_request = FriendRequest(sender = current_user, receiver = receiver)
                friend_request.save()
                data['result'] = REQUEST_SUCCESS
            if data['result'] == None:
                data['result'] = ERROR
        else:
            data['result'] = NO_USER_ID
        friendrequest_view_method = 'friend_request_operations'
        ui_update_method = 'my_request_ui_update'
        btn_room_group_name = "friend_request_"+room_name_postfix
        ui_update_room_name = "ui_update_"+str(thread_obj.id)
        print(ui_update_room_name)
        perform_broadcast(data,btn_room_group_name,friendrequest_view_method)
        perform_broadcast(data,ui_update_room_name,ui_update_method)
        return JsonResponse(data)
    else:
        return HttpResponse("In case koi batho huna khojyo vane ...all the best")
        
    
        
@login_required
def cancel_request(request):
    current_user = request.user
    data = {}
    if request.is_ajax() and request.method=="POST":
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            receiver = CustomUser.objects.get(pk = user_id)
            thread_obj = FriendRequestThread.objects.get_or_create_personal_thread(current_user,receiver)
            print("this is thread object",thread_obj)
            room_name_postfix = receiver.username
            try:
                friend_requests = FriendRequest.objects.get(sender = current_user, receiver = receiver, is_pending =True)
                friend_requests.cancel_request_by_sender()
                data['result'] = REQUEST_CANCEL
            except FriendRequest.DoesNotExist:
                data['result'] = NOTHING_TO_CANCEL
        else:
            data['result'] = NO_USER_ID
        friendrequest_view_method = 'friend_request_operations'
        btn_room_group_name = "friend_request_"+room_name_postfix
        ui_update_room_name = "ui_update_"+str(thread_obj.id)
        ui_update_method = 'my_request_ui_update'
        perform_broadcast(data,ui_update_room_name,ui_update_method)
        perform_broadcast(data,btn_room_group_name,friendrequest_view_method)    
        return JsonResponse(data)
    else:
        return HttpResponse("In case koi batho huna khojyo vane ...All the best dude")

            
@login_required
def accept_request(request, *args, **kwargs):
    current_user = request.user
    data = {}
    if request.is_ajax():
        friend_request_id = kwargs.get("friend_request_id")
        if friend_request_id:
            try:
                friend_request = FriendRequest.objects.get(pk = friend_request_id,is_pending=True)
                thread_obj = FriendRequestThread.objects.get_or_create_personal_thread(current_user,friend_request.sender)

                room_name_postfix = friend_request.sender.username
                if friend_request.receiver == current_user:
                    friend_request.accept_request()
                    data['result'] = REQUEST_ACCEPTED
                else:
                    data['result'] = NOT_YOUR_REQUEST
            except FriendRequest.DoesNotExist:
                data['result'] = NO_REQUEST_TO_ACCEPT
        else:
            data['result'] = ERROR
        try:
            friend_list = FriendList.objects.get(user = friend_request.sender)
        except FriendList.DoesNotExist:
            return HttpResponse(f"Friend list not available")
        friends = []
        current_user_friend_list = FriendList.objects.get(user = current_user)
        for friend in friend_list.friends.all():
            item = {
                'id':friend.id,
                'first_name':friend.first_name,
                'last_name':friend.last_name,
                'profile_image':friend.profile_image.url,
                'username':friend.username,
            }
            friends.append((item, current_user_friend_list.is_mutual_friend(friend)))
        data['friends'] = friends
        friendrequest_view_method = 'friend_request_operations'
        btn_room_group_name = "friend_request_"+room_name_postfix
        print(btn_room_group_name)
        ui_update_room_name = "ui_update_"+str(thread_obj.id)
        ui_update_method = 'my_request_ui_update'
        perform_broadcast(data,ui_update_room_name,ui_update_method)
        perform_broadcast(data,btn_room_group_name,friendrequest_view_method)
        return JsonResponse(data)
    else:
        return HttpResponse("In case koi batho huna khojyo vane ...All the best dude")

    

@login_required
def decline_request(request, *args, **kwargs):
    current_user = request.user
    data = {}
    if request.is_ajax():
        print("Request decline gardai")
        friend_request_id = kwargs.get('friend_request_id')
        if friend_request_id:
            try:
                friend_request = FriendRequest.objects.get(pk = friend_request_id,is_pending =True)
                thread_obj = FriendRequestThread.objects.get_or_create_personal_thread(current_user,friend_request.sender)
                room_name_postfix = friend_request.sender.username
                if friend_request.receiver == current_user:
                    friend_request.decline_request()
                    data['result'] = REQUEST_DECLINED
                else:
                    data['result'] = NOT_YOUR_REQUEST
            except FriendRequest.DoesNotExist:
                data['result'] = NO_REQUEST_TO_DECLINE
        else:
            data['result'] = ERROR
    else:
        return HttpResponse("In case koi batho huna khojyo vane ...All the best dude")
    friendrequest_view_method = 'friend_request_operations'
    btn_room_group_name = "friend_request_"+room_name_postfix
    ui_update_room_name = "ui_update_"+str(thread_obj.id)
    ui_update_method = 'my_request_ui_update'
    perform_broadcast(data,ui_update_room_name,ui_update_method)
    perform_broadcast(data,btn_room_group_name,friendrequest_view_method)
    return JsonResponse(data)


@login_required
def remove_friend(request, *args,**kwargs):
    current_user = request.user
    data = {}
    if request.is_ajax() and request.method=="POST":
        user_id = request.POST.get('removee_user_id')
        if user_id:
            try:
                user_to_be_removed = CustomUser.objects.get(pk = user_id)
                try:
                    friend_list = FriendList.objects.get(user = user_to_be_removed)
                except FriendList.DoesNotExist:
                    return HttpResponse(f"Friend list not available")
                thread_obj = FriendRequestThread.objects.get_or_create_personal_thread(current_user,user_to_be_removed)

                room_name_postfix = current_user.username
                friend_list = FriendList.objects.get(user = current_user)
                friend_list.unfriend(user_to_be_removed)
                data['result'] = FRIEND_REMOVED
            except Exception as e:
                data['result'] = f"Something went wrong: {str(e)}"
        else:
            data['result'] = NO_USER_ID

        
        friends = []
        current_user_friend_list = FriendList.objects.get(user = current_user)
        for friend in friend_list.friends.all():
            item = {
                'id':friend.id,
                'first_name':friend.first_name,
                'last_name':friend.last_name,
                'profile_image':friend.profile_image.url,
                'username':friend.username,
            }
            friends.append((item, current_user_friend_list.is_mutual_friend(friend)))
        data['friends'] = friends
        print("remove friend ko ",data['friends'])
        friendrequest_view_method = 'friend_request_operations'
        btn_room_group_name = "friend_request_"+room_name_postfix
        print("yo btn room group",btn_room_group_name)
        ui_update_room_name = "ui_update_"+str(thread_obj.id)
        ui_update_method = 'my_request_ui_update'
        perform_broadcast(data,btn_room_group_name,friendrequest_view_method)
        perform_broadcast(data,ui_update_room_name,ui_update_method)
        return JsonResponse(data)
    else:
        return HttpResponse("In case koi batho huna khojyo vane ...All the best dude")
