from .models import PrivateChatThread,PrivateChatMessage,GroupChatMessage
from django.dispatch import receiver
from django.db.models.signals import pre_save

@receiver(pre_save, sender = PrivateChatMessage)
def update_PrivateChatThread(sender, instance, **kwargs):
    instance.chat_thread.save()

@receiver(pre_save, sender = GroupChatMessage)
def update_GroupChatThread(sender, instance, **kwargs):
    instance.gc_thread.save()