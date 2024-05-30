"""ChatApp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from accounts.views import register_user,login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chat/',include('core.urls',namespace='core')),
    path('account/',include('accounts.urls',namespace='accounts')),
    path('friends/',include('friends.urls',namespace='friends')),

    path('',login_view,name="login"),
    path('register/',register_user, name="signup"),
    path("logout/", auth_views.LogoutView.as_view(next_page='login'), name="logout"),


    #Debug toolbar
    # path('__debug__/', include('debug_toolbar.urls')),
]
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)