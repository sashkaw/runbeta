from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from . import views

app_name = "getdata"

urlpatterns = [
  path("", views.getStravaData, name="getstravadata"),
  #path("details/", views.details, name="details"),
]
