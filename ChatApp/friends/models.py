from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.conf import settings
from django.db.models.deletion import CASCADE
from django.utils import timezone
from django.db.models import signals
from django.dispatch import receiver
from ChatApp.broadcast import perform_broadcast
from ChatApp.settings import AUTH_USER_MODEL
from django.db.models import Count
from django.db.models import Q
from core.models import PrivateChatThread
# Create your models here.
class FriendList(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete = models.CASCADE,related_name='user')
    friends = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='friends')

    def __str__(self):
        return self.user.username

    def add_friend(self, other_user):
        try:
            self.friends.add(other_user)
            self.save()
            
        except:
            raise ValueError
        # if not other_user in self.friends.all():
        #     self.friends.add(other_user)
        #     self.save()
        chat_thread = PrivateChatThread.objects.create_room_if_none(self.user,other_user)
        print(chat_thread)
        if not chat_thread.is_active:
            chat_thread.is_active = True
            chat_thread.save()
    
    def remove_friend(self, other_user):
            self.friends.remove(other_user)
            self.save()
            '''
            logic for Deactivating the private chat between the removed friend users
            '''
            chat_thread = PrivateChatThread.objects.create_room_if_none(self.user,other_user)
            if chat_thread.is_active:
                chat_thread.is_active = False
                chat_thread.save()

    def unfriend(self, user_to_be_removed):
        remover_friends_list = self
        #Remove garne manche ko friend list bata friend lai remove garne
        remover_friends_list.remove_friend(user_to_be_removed)
        #jaslai remove gariyeko cha tesko bata ni unfriend garauna parcha
        friends_list = FriendList.objects.get(user = user_to_be_removed)#to be removed user ko friend list
        friends_list.remove_friend(remover_friends_list.user)

    
    def get_friends(self):
        return " , ".join([str(p) for p in self.friends.all()])

    def is_mutual_friend(self, friend):
        if friend in self.friends.all():
            return True
        else:
            return False



class FriendRequestManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by('-updated_at')


class FriendRequest(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE, related_name = 'request_sender')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = CASCADE, related_name='request_receiver')
    is_pending = models.BooleanField(blank = False, null=False, default=True)
    timestamp = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = FriendRequestManager()

    class Meta:
        ordering = ['-updated_at']


    def __str__(self):
        return self.sender.username

    def accept_request(self):
        receiver_friend_list = FriendList.objects.get(user = self.receiver)
        if receiver_friend_list:
            receiver_friend_list.add_friend(self.sender)
            sender_friend_list = FriendList.objects.get(user = self.sender)
            if sender_friend_list:
                sender_friend_list.add_friend(self.receiver)
                self.is_pending = False
                self.save()

    def decline_request(self):
        self.is_pending = False
        self.save()

    def cancel_request_by_sender(self):
        self.is_pending = False
        self.save()

class TrackingModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        abstract = True

class FriendRequestThreadManager(models.Manager):
    def get_or_create_personal_thread(self, user1, user2):
        if user1 == user2:
            return False
        has_thread = FriendRequestThread.objects.filter(Q(req_user1 = user1,req_user2 = user2)| Q(req_user1=user2,req_user2=user1)).first()
        print("yo found vako has thread",has_thread)
        if has_thread:
            return has_thread
        elif not has_thread:
            print("not found so creating the request thread")
            created_thread = FriendRequestThread.objects.create(req_user1=user1,req_user2=user2)
            return created_thread



    def by_user(self, user):
        return self.get_queryset().filter(request_connected_users__in=[user])


class FriendRequestThread(TrackingModel):
    req_user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='request_user1')
    req_user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True,blank=True,related_name='request_user2')
    request_connected_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,related_name="request_connected_users")
    is_active = models.BooleanField(default=False)

    objects = FriendRequestThreadManager()

    def connect(self,user):
        is_added = False
        if not user in self.request_connected_users.all():
            self.request_connected_users.add(user)
            is_added = True
        return is_added
    
    def disconnect(self,user):
        is_removed = False
        if not user in self.request_connected_users.all():
            self.request_connected_users.remove(user)
            is_removed = True
        return is_removed

    def __str__(self)->str:
        return f'Request :{self.req_user1} - {self.req_user2}'


@receiver([signals.post_save],sender=FriendRequest)
def notify_group(sender, instance, **kwargs):
    from accounts.models import CustomUser

    room_name_postfix = instance.receiver.username
    group_name = "friend_request_"+room_name_postfix
    consumer_method_type = 'friend_request_operations'
    if not kwargs['created']:
        data = {}
        friend_requests = FriendRequest.objects.filter(receiver=instance.receiver, is_pending = True)
        sender_ids = friend_requests.values('sender_id')
        print(sender_ids)
        sender_qs = CustomUser.objects.filter(id__in = sender_ids).order_by('request_sender')
        print("khai yesle kaam garekai chaina jasto cha")
        data['sender'] = list(sender_qs.values(
            'username',
            'first_name',
            'last_name',
            'id',
            'profile_image',
            ))
        
        data['friend_requests'] = list(friend_requests.values('id','receiver','sender'))
        perform_broadcast(data,group_name,consumer_method_type)
        pass
    elif kwargs['created']:
        data = {}
        friend_requests = FriendRequest.objects.filter(receiver=instance.receiver, is_pending = True)
        sender_ids = friend_requests.values('sender_id')
        sender_qs = CustomUser.objects.filter(id__in = sender_ids)
        data['sender'] = list(sender_qs.values(
            'username',
            'first_name',
            'last_name',
            'id',
            'profile_image',
            ))
        data['friend_requests'] = list(friend_requests.values('id','receiver','sender'))
        print("yo chai new create vako")
        perform_broadcast(data,group_name,consumer_method_type)



