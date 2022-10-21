from django.db import models
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.gis.db import models
#from django.conf import settings

import time
#import pickle
#import os
#import dotenv
#from dotenv import load_dotenv
import datetime
from pandas import to_numeric
import polyline
#from pathlib import Path

# Create your models here.

# Customize model initiation with use of manager -> preferred for Django instead of overriding '__init__'
class RouteManager(models.Manager):
  def create_route(self, user, route, date, distance, line):
    new_route = self.create(
      user_id=user,
      route_id=route,
      date=date,
      distance=distance,
      line=line,
    )
    
    # Return the route object 
    return new_route

# Class Route
class Route(models.Model):
  # User name --> not sure if required
  user_id = models.ForeignKey(User, on_delete = models.CASCADE)
  # Name of route
  route_id = models.CharField(max_length = 200)
  # Route date
  date = models.DateTimeField("date completed")
  # Route length
  distance = models.IntegerField()
  # Spatial geometry of route
  line = models.LineStringField()
  # Use RouteManager to initialize Route object with data
  objects = RouteManager()

  def __str__(self):
    return self.route_id


class Elevation(models.Model):

  # Route name
  route_id = models.ForeignKey(Route, on_delete = models.CASCADE)

  # Define fields for elevation data
  # elevation_x_coord = models.FloatField()
  # elevation_y_coord = models.FloatField()
  # elevation_z_coord = models.FloatField()

  # Define field to 
  xyz_point = models.PointField()
   
  def __str__(self):  
    return self.route_id

  def getElevationData():
    # TODO: add method for getting x,y,z data from strava and calling Point(x, y, z)
    # from GEOS api docs: class Point(x=None, y=None, z=None, srid=None)¶
    pass