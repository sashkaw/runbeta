# Django imports
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField

# Load libraries
import time
import datetime
from pandas import to_numeric

# Customize model initiation with use of manager -> preferred for Django instead of overriding '__init__'
class ActivityManager(models.Manager):
  def create_activity(self, user, activity, start_date, created_date, line):
    new_activity = self.create(
      user_id=user,
      activity_id=activity,
      start_date=start_date,
      created_date=created_date,
      line=line,
    )
    
    # Return the activity object 
    return new_activity

# Class Activity
class Activity(models.Model):

  # User ID
  # Note: Set db_column to "user_id", otherwise col name is "user_id_id"
  user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")

  # Name of activity
  activity_id = models.CharField(max_length=200)

  # Activity date
  start_date = models.DateTimeField(null=True, help_text="date started")

  # Date added to RunBeta database
  created_date = models.DateTimeField(null=True, help_text="date added to database")

  # Activity stream data
  time = ArrayField(base_field=models.TimeField(null=True, blank=True, help_text="time elapsed"), null=True)
  # Note: Had to delete all old migrations except for the first '0001 init', the root level data/ folder and pycache folders to get this latlng migration to work
  latlng = models.MultiPointField(null=True, blank=True, help_text="latlng position") 
  distance = ArrayField(base_field=models.FloatField(null=True, blank=True, help_text="distance from start"), null=True)
  altitude = ArrayField(base_field=models.FloatField(null=True, blank=True, help_text="time elapsed"), null=True)
  velocity_smooth = ArrayField(base_field=models.FloatField(null=True, blank=True, help_text="velocity smooth"), null=True)
  heartrate = ArrayField(base_field=models.FloatField(null=True, blank=True, help_text="heart rate"), null=True)
  cadence = ArrayField(base_field=models.FloatField(null=True, blank=True, help_text="cadence"), null=True)
  watts = ArrayField(base_field=models.FloatField(null=True, blank=True, help_text="watts"), null=True)
  temp = ArrayField(base_field=models.FloatField(null=True, blank=True, help_text="temperature"), null=True)
  moving = ArrayField(base_field=models.FloatField(null=True, blank=True, help_text="moving"), null=True)
  grade_smooth = ArrayField(base_field=models.FloatField(null=True, blank=True, help_text="grade smooth"), null=True)

  # Elevation sampling points (shouldn't need this since we have latlng data)
  #elevation_sampling_points = ArrayField(base_field=models.PointField(null=True, blank=True, help_text="elevation sampling points"), null=True)

  #Elevation data
  elevation = ArrayField(base_field=models.FloatField(null=True, blank=True, help_text="elevation values"), null=True)
  
  # Spatial geometry of route
  line = models.LineStringField(null=True, blank=True, help_text="activity path")
  
  # Use manager to initialize Activity object with data
  objects = ActivityManager()

  # Define unique combination of values for user_id and route_id to avoid duplicates
  # Note: This migration will only work if you delete previous duplicate entries in the database
  class Meta:
    unique_together = ["user_id", "activity_id"]

  def __str__(self):
    return self.activity_id