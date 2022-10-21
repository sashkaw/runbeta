"""runbeta URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.urls import include, path
from django.contrib.auth import views as auth_views
from register import views as register_views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Note: the default login view will search through the "templates" folders looking for a folder called "registration" with a login.html file inside
    path("login/", auth_views.LoginView.as_view(), name = "login"), # Same currently as authstrava/login
    path("logout/", auth_views.LogoutView.as_view(), name = "logout"),
    path("register/", include("register.urls")), 
    path("getdata/", include("getdata.urls")),
    path("oauth/", include("social_django.urls", namespace="social")), # to do -> link this with template??
]
