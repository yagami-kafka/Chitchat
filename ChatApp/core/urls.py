from django.urls import path
from django.urls.resolvers import URLPattern
from django.urls import reverse_lazy
from . import views
from accounts.views import search_user

app_name = "core"

urlpatterns = [
    path('',views.chat_thread_view,name = 'conversation'),
    path('search/',search_user, name='search'),
    path('test_room/', views.test_room_view, name='private-chat-room'),
    path('create_or_return_private_chat/',views.create_or_return_private_chat, name='create-or-return-private-chat'),
    path('add_member_search/',views.add_member_search, name='add-member-search'),
    path('chat_thread_list/',views.ThreadViewSet.as_view({'get':'list'}) , name='chat-thread-list'),
    path('create_group_chat/',views.create_group_chat,name = 'create-group-chat'),
    path('update_group_chat_name/',views.update_group_chat_name,name= 'update-group-chat-name'),
    path('update_group_chat_photo/',views.update_group_chat_photo,name= 'update-group-chat-photo'),
    path('add_new_members/',views.add_members_to_chat,name='add-new-members'),
    path('remove_group_member/',views.remove_group_member,name='remove-group-member'),
    path('leave_group/',views.leave_group,name='leave-group'),
    path('generate_keys/',views.generate_keys,name='generate-keys'),
    path('gsk/',views.gsk,name='generate-shared-keys'),
    path('test_api/',views.test_api,name= 'test-api'),
]