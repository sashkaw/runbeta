from django.urls import path
from . import views

APP_NAME = "register"

urlpatterns = [
  path('', views.register, name='register'),
]