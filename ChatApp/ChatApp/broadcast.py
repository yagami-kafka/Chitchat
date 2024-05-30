from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json

def perform_broadcast(data,consumer_room_group,consumer_method_type):
    channel_layer = get_channel_layer()
    print("perform broadcast ko ",consumer_room_group,consumer_method_type)
    async_to_sync(channel_layer.group_send)(
        consumer_room_group,
        {
            'type':consumer_method_type,
            'content':json.dumps(data),
        }
    )