from django.contrib import admin

from .models import *

class PrivateChatMessageAdmin(admin.ModelAdmin):
    model = PrivateChatMessage
    list_display = ['chat_thread','sender','message_content','message_type','timestamp']


class PrivateChatThreadAdmin(admin.ModelAdmin):
    model = PrivateChatThread
    list_display = ['first_user','second_user','is_active','get_connected_users']

class GroupChatThreadAdmin(admin.ModelAdmin):
    model = GroupChatThread
    list_display = ['group_name','image','group_description','admin','id','get_members']

    # def get_members(self):
    #     my_group = Group.objects.get(id = self.id)
    #     return my_group.user_set

class KeysAdmin(admin.ModelAdmin):
    model = Keys
    list_display = ['keys_owner',]


admin.site.register(GroupChatThread,GroupChatThreadAdmin)
admin.site.register(PrivateChatThread,PrivateChatThreadAdmin)
admin.site.register(GroupChatMessage)
admin.site.register(GroupJoinedDate)
# admin.site.register(Keys,KeysAdmin)
admin.site.register(PrivateChatMessage,PrivateChatMessageAdmin)


# Register your models here.
