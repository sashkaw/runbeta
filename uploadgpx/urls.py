from django.urls import path

from . import views

APP_NAME = "uploadgpx"

urlpatterns = [
    path('',views.upload_gpx, name='index'),
]