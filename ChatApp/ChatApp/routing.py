from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from django.urls import path, re_path
from friends.consumers import (ButtonConsumer,FriendRequestsConsumer,)
from core.consumers import GroupChatConsumer, PrivateChatConsumer, ThreadListUpdateConsumer
from accounts.consumers import IndividualConsumer
websocket_urlPattern = [
    re_path(r'ws/friendrequest/(?P<room_name>\w+)/$',ButtonConsumer.as_asgi()),
    re_path(r'ws/uiupdate/(?P<username>\w+)/$',FriendRequestsConsumer.as_asgi()),
    re_path(r'ws/privatechat/(?P<friendId>\w+)/$',PrivateChatConsumer.as_asgi()),
    re_path(r'ws/groupchat/(?P<groupThreadId>\w+)/$',GroupChatConsumer.as_asgi()),
    re_path(r'ws/tu/(?P<uid>\w+)/$',ThreadListUpdateConsumer.as_asgi()),
    re_path(r'ws/a_&_i/',IndividualConsumer.as_asgi()),#for active inactive status of user

]

application=ProtocolTypeRouter({
    #'http':
    'websocket':AuthMiddlewareStack(URLRouter(websocket_urlPattern)),
})