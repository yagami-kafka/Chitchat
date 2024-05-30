from django.utils import timezone
from datetime import datetime
from django.contrib.humanize.templatetags.humanize import naturalday
from django.core.serializers.python import Serializer

DEFAULT_PAGE_SIZE = 30
MSG_TYPE_NORMAL = 0 
MSG_TYPE_ADDED = 1
MSG_TYPE_REMOVED = 2
CHAT_PHOTO_CHANGED = 3
CHAT_NAME_CHANGED = 4


MEMBER_ADDED = "M_A"
MEMBER_REMOVED  = "M_R"
GROUP_LEFT = "G_L"


MEMBERS_ACTION = [MEMBER_ADDED,MEMBER_REMOVED,GROUP_LEFT]

def timestamp_encoder(timestamp):

    ts = ''
    #for showing today or yesterday 
    if(naturalday(timestamp) == 'today') or (naturalday(timestamp) == 'yesterday'):
        str_time = datetime.strftime(timestamp, "%I:%M %p")
        str_time = str_time.strip("0")
        ts = f"{naturalday(timestamp).capitalize()} : {str_time}"

    else:
        str_time = datetime.strftime(timestamp, "%m/%d/%Y")
        ts = f"{str_time}"
        

    return str(ts)

class LazyPrivateThreadMessageEncodeer(Serializer):
    def get_dump_object(self, obj):
        dump_object = {}
        dump_object.update({'msg_id': str(obj.id)})
        dump_object.update({'user_id':str(obj.sender.id)})
        dump_object.update({'username': str(obj.sender.username)})
        dump_object.update({'first_name':str(obj.sender.first_name)})
        dump_object.update({'last_name': str(obj.sender.last_name)})
        dump_object.update({'profile_image': str(obj.sender.profile_image.url)})
        dump_object.update({'message_content': str(obj.message_content)})
        dump_object.update({'natural_timestamp': timestamp_encoder(timezone.localtime(obj.timestamp))})
        return dump_object

class LazyGroupThreadMessageEncodeer(Serializer):
    def get_dump_object(self, obj):
        dump_object = {}
        dump_object.update({'msg_type':MSG_TYPE_NORMAL})
        dump_object.update({'msg_id': str(obj.id)})
        dump_object.update({'user_id':str(obj.sender.id)})
        dump_object.update({'username': str(obj.sender.username)})
        dump_object.update({'first_name':str(obj.sender.first_name)})
        dump_object.update({'last_name': str(obj.sender.last_name)})
        dump_object.update({'profile_image': str(obj.sender.profile_image.url)})
        dump_object.update({'message_content': str(obj.content)})
        dump_object.update({'natural_timestamp': timestamp_encoder(timezone.localtime(obj.timestamp))})
        return dump_object