from email.headerregistry import Group
from django.contrib.auth.models import User
from accounts.models import CustomUser
from rest_framework import serializers
from .models import GroupChatMessage, PrivateChatMessage, PrivateChatThread,GroupChatThread

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id','username','first_name','last_name','profile_image',]

class PrivateChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivateChatMessage
        fields = ['id','sender','message_content']
class GroupChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupChatMessage
        fields = ['id','sender','content']

class GroupChatThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupChatThread
        fields = ['id','name','group_name','image','updated_at','admin','latest_msg']
    # def get_latest_msg(self,obj):
    #     msg = obj.last_msg()
    #     msg_serializer = GroupChatMessageSerializer(msg)
    #     return msg_serializer.data

class PrivateChatThreadSerializer(serializers.ModelSerializer):
    first_user = UserSerializer(read_only = True)
    second_user = UserSerializer(read_only = True)
    last_msg = serializers.SerializerMethodField(read_only = True)

    class Meta:
        model = PrivateChatThread
        fields = ['id','first_user','second_user','updated_at','last_msg']
    def get_last_msg(self,obj):
        msg =  obj.last_msg()
        last_msg_serializer = PrivateChatMessageSerializer(msg)
        return last_msg_serializer.data