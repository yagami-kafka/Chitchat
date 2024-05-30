from django.urls import path
from friends.views import(
    remove_friend,
    send_request,
    cancel_request,
    friend_requests,
    accept_request,
    decline_request,
    view_friend_list,
    remove_friend,
)

app_name = "friends"

urlpatterns = [
    path('view_friend_list/<userId>/',view_friend_list,name='friend-list'),
    path('view_friend_requests/<userId>/',friend_requests, name='friend-requests'),
    path('send_request/',send_request, name='send-friend-request'),
    path('cancel_request/',cancel_request, name = 'cancel-friend-request'),
    path('accept_request/<friend_request_id>/',accept_request, name='accept-friend-request'),
    path('decline_request/<friend_request_id>/',decline_request,name='decline-friend-request'),
    path('remove_friend/',remove_friend,name='unfriend'),
    
]