from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from . import views

app_name = "getdata"

urlpatterns = [
  path("strava/", views.render_strava_data, name="getdata-strava"),
  #path("details/", views.details, name="details"),
  path("earth/", views.render_earth_data, name = "getdata-earth"),
]
