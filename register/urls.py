from django.urls import path
from . import views

APP_NAME = "register"

urlpatterns = [
  path('', views.register, name='index'),
  path("home/", views.home, name="home"),
  path("details/", views.details, name="details"),
  path("settings/", views.settings, name="settings"),
  path("settings/password/", views.password, name="password"),
]