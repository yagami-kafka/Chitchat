from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email','first_name','last_name', 'is_staff','is_admin','hide_email', 'is_active','is_superuser','profile_image','date_joined','last_login','id','username','status')
    list_filter = ('email', 'is_staff', 'is_active','is_superuser','date_joined','username',)
    fieldsets = (
        (None, {'fields': ('first_name','last_name','email','username','profile_image','password','hide_email')}),
        ('Permissions', {'fields': ('is_staff', 'is_active','is_admin')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name','last_name','email','username','password1', 'password2','hide_email','profile_image','is_staff', 'is_active','is_admin')}
        ),
    )
    search_fields = ('email','username','first_name','last_name')
    ordering = ('email','username','first_name','last_name')

admin.site.register(CustomUser, CustomUserAdmin)