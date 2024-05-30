from enum import unique
from django.db import models
from django.contrib.auth.models import Group
from django.conf import settings
from django.db.models.base import ModelState
from django.db.models.fields import related
from django.utils import tree
from django.db.models import Q
# Create your models here.

class PrivateChatManager(models.Manager):
    def create_room_if_none(self,user1,user2):
        chat_thread = PrivateChatThread.objects.filter(Q(first_user = user1, second_user = user2) | 
        Q(first_user = user2, second_user = user1)
        ).first()
        if not chat_thread:
            print("not found private chat")
            chat_thread = PrivateChatThread.objects.create(first_user = user1, second_user = user2)
            chat_thread.save()
        return chat_thread

    # def by_user(self, **kwargs):
    #     user = kwargs.get('user')
    #     lookup = Q(first_user = user) | Q(second_user = user)
    #     qs = self.get_queryset().filter(lookup).distinct()
    #     return qs

class PrivateChatThread(models.Model):
    first_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='thread_first_person')
    second_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True,blank=True,related_name='other_user')
    connected_users = models.ManyToManyField(settings.AUTH_USER_MODEL,blank = True, related_name="private_connected_users")
    is_active = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)

    objects = PrivateChatManager()
    class Meta:
        unique_together = ['first_user','second_user']

    def __str__(self) -> str:
        return f'chat thread {self.first_user} {self.second_user}'
    def get_connected_users(self):
        return " , ".join([str(p) for p in self.connected_users.all()])

    def connect(self,user):
        is_added = False
        if not user in self.connected_users.all():
            self.connected_users.add(user)
            is_added = True
            print("ok added")
        return is_added

    def disconnect(self,user):
        is_removed = False
        if user in self.connected_users.all():
            self.connected_users.remove(user)
            is_removed = True
            print("ok removed")
        return is_removed
    
    def last_msg(self):
        return self.private_message.all().last()
    @property
    def latest_msg(self):
        try:
            msg = self.private_message.all().last().id
            print("this is private msg",msg)
            msg_sender = self.private_message.all().last().sender.first_name
            print("msg sender",msg_sender)
            return msg_sender+":"+str(msg)
        except:
            msg = "No messages have been exchanged yet."
            return msg
class PrivateChatMessageManager(models.Manager):
    def by_private_thread(self, private_thread):
        qs = PrivateChatMessage.objects.filter(chat_thread=private_thread).order_by('-timestamp')
        return qs

class PrivateChatMessage(models.Model):
    chat_thread = models.ForeignKey(PrivateChatThread, null=True,blank=True, on_delete=models.CASCADE,related_name="private_message")
    sender= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='msg_sender')
    message_content = models.TextField(unique=False,blank=False,null=True) 
    message_type = models.CharField(max_length=50,null=True,blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = PrivateChatMessageManager()

class GroupChatThread(Group):
    group_name = models.CharField(max_length=100,null=True)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL,null=True, on_delete=models.SET_NULL, related_name ='grpadmin')
    image = models.ImageField(default='group_photos/nouser.jpg',upload_to='group_photos')
    group_description = models.TextField(blank=True, help_text="description of the group")
    created_at = models.DateTimeField(auto_now_add=True,auto_now=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.group_name

    def add_members(self,group_chat,members):
        for m in members:
            group_chat.user_set.add(m)
    def last_msg(self):
        return self.gc_message.all().last()
    @property
    def latest_msg(self):
        try:
            msg = self.gc_message.all().last().content
            msg_sender = self.gc_message.all().last().sender.first_name
            return msg_sender+":"+msg
        except:
            msg = "No messages have been exchanged yet."
            return msg
    
    @property
    def gc_name(self):
        return "GroupChat-%s" % self.id
    def get_members(self):
        my_group = Group.objects.get(id = self.id)
        return " , ".join([str(p) for p in my_group.user_set.all()])

class GroupChatMessageManager(models.Manager):
    def by_gc_thread(self, gc_thread):
        qs = GroupChatMessage.objects.filter(gc_thread=gc_thread).order_by("-timestamp")
        return qs

class GroupJoinedDate(models.Model):
    gc = models.ForeignKey(GroupChatThread,on_delete=models.CASCADE,related_name='gc_joined')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='grp_joined_user')
    joined_date = models.DateTimeField(auto_now_add=True,auto_now=False)
    updated_joined_date = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return f'{self.user.username} joined {self.gc.group_name} on {self.joined_date} / {self.updated_joined_date}'

class GroupChatMessage(models.Model):
    gc_thread = models.ForeignKey(GroupChatThread,on_delete=models.CASCADE,related_name='gc_message')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='grp_sender')
    timestamp = models.DateTimeField(auto_now_add=True)
    message_type = models.CharField(max_length=50, blank=True, null= True, default='text')
    content = models.TextField(unique=False,blank=False)

    objects = GroupChatMessageManager()

    def __str__(self):
        return self.content + self.sender.username

class Keys(models.Model):
    keys_owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='keys_owner')
    private_key = models.TextField(blank=True,null=True)
    second_private_key = models.TextField(blank=True,null=True)
    public_key = models.TextField(blank=True,null=True)