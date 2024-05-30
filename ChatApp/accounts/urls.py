from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path('profile/<userId>',views.view_profile,name='profile'),
    path('profile/edit/<userId>',views.update_profile, name='profile_update'),
]