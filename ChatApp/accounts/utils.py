from django.core.serializers.json import DjangoJSONEncoder, Serializer
from django.core.serializers import serialize
from .models import CustomUser
class LazyCustomUserEncoder(Serializer):
    def get_dump_object(self, obj):
        dump_object = {}
        dump_object.update({'id': str(obj.id)})
        dump_object.update({'username': str(obj.username)})
        dump_object.update({'profile_image': str(obj.profile_image.url)})
        dump_object.update({'first_name': str(obj.first_name)})
        dump_object.update({'last_name': str(obj.last_name)})
        return dump_object

