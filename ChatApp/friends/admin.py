from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from .models import FriendList,FriendRequest,FriendRequestThread

class FriendRequestAdmin(admin.ModelAdmin):
    model = FriendRequest
    list_display = ('sender','receiver','is_pending','id','timestamp','updated_at')
    list_filter = ('sender','receiver','is_pending',)

class FriendListAdmin(admin.ModelAdmin):
    model = FriendList
    list_display = ('user','get_friends',)
    list_filter = ('user',)

    # def get_friends(self,obj):
    #     return "\n".join([p.friends for p in obj.friends.all()])

class FriendRequestThreadAdmin(admin.ModelAdmin):
    model = FriendRequestThread
    list_display = ('id','req_user1','req_user2')

admin.site.register(FriendRequest,FriendRequestAdmin)
admin.site.register(FriendList,FriendListAdmin)
admin.site.register(FriendRequestThread,FriendRequestThreadAdmin)