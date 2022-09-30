from django.db import models
from django.utils import timezone
from django.contrib import admin
import datetime

# Create your models here.

#to store different users
class User(models.Model):
  def __str__(self):
    return self.user_name

  #check if user was created recently
  def was_created_recently(self):
    now = timezone.now()
    return now - datetime.timedelta(days=1) <= self.creation_date <= now

  #user data
  user_name = models.CharField(max_length = 200)
  creation_date = models.DateField("date created")

#to store different logged routes
class Route(models.Model):
  def __str__(self):
    return self.route_name

  #link route with user
  user = models.ForeignKey(User, on_delete = models.CASCADE)
  #name of route
  route_name = models.CharField(max_length=200)
  #route date
  date = models.DateTimeField("date completed")
