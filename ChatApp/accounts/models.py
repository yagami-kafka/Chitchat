from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
from friends.models import FriendList
from core.DoubleDiffie import DiffieHellman
from core.models import Keys

# Create your models here.

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, username, password, **extra_fields):
        """
        Create and save a User with the given email username and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        if not username:
            raise ValueError(_('The username must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email,username = username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email,username, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_admin',True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email,username, password, **extra_fields)

DEFAULT = 'user_photos/nouser.jpg'
class CustomUser(AbstractUser):
    email                   = models.EmailField(_('email address'), unique=True)
    username                = models.CharField(max_length=30, unique=True)
    date_joined				= models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    last_login				= models.DateTimeField(verbose_name='last login', auto_now=True)
    is_admin				= models.BooleanField(default=False)
    is_active				= models.BooleanField(default=True)
    is_staff				= models.BooleanField(default=False)
    is_superuser			= models.BooleanField(default=False)
    profile_image			= models.ImageField(max_length=255, upload_to='user_photos', null=True, blank=True, default=DEFAULT)
    hide_email				= models.BooleanField(default=True)
    status                  = models.IntegerField(default=0)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username','first_name','last_name']

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        super().save(*args,**kwargs)
        SIZE = 300,300
        print("yaa samma chai ma ni ho hai")
        if self.profile_image and hasattr(self.profile_image, 'url'):
            print(self.profile_image.path)
            try:
                pic = Image.open(self.profile_image.path)
                print(" ma chai herna aako")
                pic.thumbnail(SIZE, Image.LANCZOS)
                pic.save(self.profile_image.path)
            except:
                print("i am here")
                self.profile_image.delete(save=False)  # delete old image file
                self.profile_image = DEFAULT
                self.save()

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj = None):
        return self.is_admin
    
    def has_module_perms(self, app_label):
        return True
    @property
    def get_photo_url(self):
        if self.profile_image and hasattr(self.profile_image, 'url'):
            return self.profile_image.url
        else:
            return "/media/user_photos/nouser.jpg"

@receiver(post_save, sender=CustomUser)
def user_save(sender, instance, **kwargs):
    FriendList.objects.get_or_create(user=instance)

# @receiver([signals.post_save],sender=CustomUser)
# def store_keys(sender, instance, **kwargs):
#     data = {}
#     dh = DiffieHellman()
#     private_key,public_key= dh.get_private_key(), dh.generate_public_key()
#     second_private_key = dh.get_second_private_key()
#     data['private_key'] = private_key
#     data['second_private_key'] = second_private_key
#     data['public_key'] = public_key
#     # return JsonResponse(data)
#     Keys(keys_owner = instance,private_key = private_key,second_private_key = second_private_key,public_key = public_key)
