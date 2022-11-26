# Django imports
import json
import os
import time
from curses.ascii import HT
from multiprocessing import context
from re import T
from tokenize import String

import ee
import folium
import numpy as np
import pandas as pd
import polyline
from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import (AdminPasswordChangeForm,
                                       PasswordChangeForm, UserCreationForm)
from django.contrib.auth.models import User
from django.contrib.gis.geos import LineString
from django.core.serializers import serialize
from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from django.views.generic import TemplateView
from dotenv import load_dotenv
from folium import Polygon, plugins
from folium.plugins import MarkerCluster
# Package imports
from social_django.models import UserSocialAuth
from social_django.utils import load_strategy
from stravalib.client import Client

# Custom models
from .models import Activity

# Constants
ELEVATION_EXTRACTION_RESOLUTION = 10
ELEVATION_DATA_NAME = "USGS/3DEP/1m"

# Create your views here.

# Check if access token is still valid, and if not refresh the token and return the new access token
def get_token(user, provider):
  social = user.social_auth.get(provider = provider)
  # the  ' - 10' is so that the token doesn't expire as we make the request 
  # if we check the token expiry right before it expires
  if (social.extra_data['auth_time'] + social.extra_data['expires'] - 10) <= int(time.time()):
      strategy = load_strategy() # Refresh token
      social.refresh_token(strategy)
  return social.extra_data['access_token']


# Function to create Folium map object
# map_data_dict should be a dictionary of the form
# {
#   <data_type>: <data>,
#   <data_type>: <data>,
# }
# data_type should be one of "polygon" for vector polygon data, "line" for vector line data, "point" for vector point data, or "raster" for raster data
# data should be a spatial data object (eg LineString, Point)
def create_map(map_data_dict, centroid):
  
  # Create web map using Folium
  #figure = folium.Figure()
  
  # Center map on the centroid passed to this function, set zoom and background tile layer
  m = folium.Map(
      location=centroid, 
      zoom_start=12,
      tiles="Stamen Terrain"
    )

  # Create feature group so we can toggle vector data on and off
  fg=folium.FeatureGroup(name='Points', show=False)
  m.add_child(fg)
  marker_cluster = MarkerCluster().add_to(fg)

  # Create map layers from the input data
  for dt, md in map_data_dict.items():

    # Create Folium layers from input data, or raise error if invalid data type
    if(dt == "point"):
      # Create markers on the map for all points in the input data 
      for point in md:
        #folium.Marker(point, control=True).add_to(m)
        folium.Marker(point, control=True).add_to(marker_cluster)

    elif(dt == "line"):
      # Create polyline and add it to the folium map
      #folium.PolyLine(md, color='red', control=True).add_to(m)
      folium.PolyLine(md, color='red', control=True).add_to(marker_cluster)

    elif(dt == "polygon"):
      folium.Polygon(md, color = "blue", control=True).add_to(m)

    elif(dt == "raster"):
      # Create Folium raster tile layer and add it to the map
      folium.raster_layers.TileLayer(
          #Get URL to the elevation data on Google Earth Engine
          tiles=md, 
          #tiles="Stamen Terrain",
          attr="Google Earth Engine",
          name=ELEVATION_DATA_NAME, # TODO: Potentially add option to pass other names and attr sources to this TileLayer() creation
          overlay=True,
          control=True,
      ).add_to(m)

    else:
      raise TypeError("In function show_map(), argument data_type is invalid. Expected one of 'polygon', 'line', 'point', or 'raster'\n")

  # Add toggle on/off for layer visibility
  folium.LayerControl().add_to(m)

  # Render the folium map
  #figure.render()
  #display(m)
  m = m._repr_html_()

  #return figure
  return m

# Below code is just a test for checking that we can get data from strava when authenticated with strava using django social auth
"""@login_required
def details(request):
  template = "getdata/details.html"
  if request.user.is_authenticated:
    strava_access_token = get_token(request.user, "strava")

    # Create new client instance with the access token we generated
    client = Client(access_token = strava_access_token)

    # get test data about athlete
    current_athlete = client.get_athlete()
    athlete_name = current_athlete.firstname + " " + current_athlete.lastname
    all_routes = client.get_routes(limit = 5)

  context = {
    "user": request.user,
    "access_token": strava_access_token,
    "current_athlete": current_athlete,
    "athlete_name" : athlete_name,
    "all_routes": all_routes,
  }
  return render(request, template, context)"""

# Function to generate points at a specified distance along lines 
# Inputs: integer step_distance (in meters)
def interpolate_points(step_distance):
  # PostGIS query to create points along a line at 10m increments 
  # The Generate_Series generates a series of numbers starting at 0, spaced apart by the default value of 1, and ending at the value equal to the (<length of the line> / 10) rounded up and cast to an integer
  # Update: don;t need to use ST_LENGTH as we already distance in meters from strava
  # CROSS JOIN creates paired combinations of the series we generated (0, 1, ..... CEIL(ST....)) to the table getdata_route, so that we now have 10 rows for each row in the original table
  # EG for the first row in getdata_route we join the first value in the series (eg route_id #1, 0), and for the second we have (route_id #1, 1) and so on through (route_id #n, CEIL(ST...))
  # Here 'line' refers to linestring in DB created from routes (see models.py) -> in other queries people often refer to this as 'geom'
  # The LEAST statement produces a distance at some fraction a long a line by multiplying the number in column n (a number from 0 to route length / 10) by (10 / length of route)
  # EG for n = 0 and length of 5000 m that would be 0 * (10 m / 5000 m) = 0
  # And for n = (5000 / 10) you get (5000 / 10) * (10 / 5000) = 1
  # We do this because ST_LineInterpolatePoint takes a float between 0 and 1 for its second argument (which is the position along the line)
  # The function then returns a point interpolated along the line at that location (eg beginning of line would be 0 and end of line would be 1)
  # The output of the function is then cast to a POINT object with EPSG:4326
  # The CREATE TABLE statement then creates a new table called points_along_routes copied from
  # the result of selecting n (a number from 0 to the length of the route divided by 10)
  # and the corresponding interpolated point we calculated above
  # Output should look something like:
  # route_id | n | point_on_route
  # 1        | 0 | <ST_Point object at start of route>
  # 2        | 1 | <ST_Point object at first step along route>
  #...
  
  # To execute raw SQL queries directly:
  interpolate_points_query = f"""CREATE TABLE points_along_routes AS (
                                  SELECT route_id,
                                        n, 
                                        ST_LineInterpolatePoint(line, LEAST(n*({step_distance}/distance), 1.0))::GEOMETRY(POINT, 4326) AS point_on_route
                                  FROM getdata_activity 
                                  CROSS JOIN 
                                    Generate_Series(0, CEIL(distance/{step_distance})::INT) AS n
                                )"""
                
  #raw_query = "select ST_GeometryType(line) from getdata_route;" # For testing that query code works
  with connection.cursor() as cursor:
    cursor.execute(interpolate_points_query)
    #raw_query_output = cursor.fetchall()
    #print(raw_query_output)

# View to test that app can connect successfull to Google Earth Engine
# Note that the area of interest should be in geojson format

test_sampling_points = {
      "type": "MultiPoint",
      "coordinates": 
      [
          [-110.71, 32.31],
          [-110.68, 32.32],
          [-110.66, 32.30]
      ]
    }

# Function to get earth raster data and sample raster values at points of interest
def get_earth_data(data_name, sample_points):

  # Get an object to work with
  #recent_route = Route.objects.get(pk=1) # For testing

  # Convert data to geojson
  #aoi_geojson = json.loads(area_of_interest.geojson)
  #aoi_geojson = json.loads(area_of_interest)
  sample_points_ee = ee.Geometry(sample_points)
  #print(aoi_ee.getInfo())

  # Get elevation data
  # Note: the USGS 3D Elevation Profile data seems to be the best
  # Elevation data that Google Earth Engine offers (at 1m resolution)
  # Extract the most recent image from the collection
  earth_data = ee.ImageCollection(data_name)

  # Get earth data tiles for area of interest (note that filterBounds does not clip the data, it just selects overlapping tiles)
  earth_data_filter_aoi = earth_data.filterBounds(sample_points_ee) # For image collection 

  # Get most recent image
  #earth_data_recent = earth_data_filter_aoi.limit(1, 'system:time_start', False).first()

  # Reduce image collection
  #earth_data_reduced = earth_data_filter_aoi.reduce(ee.Reducer.max())
  
  # Get max value (returns image)
  earth_data_max = earth_data_filter_aoi.max()

  # Sample earth data at points of interest
  #earth_data_sample = earth_data_max.sample(sample_points_ee)
  earth_data_clipped = earth_data_max.clip(sample_points_ee)
  # TODO: Figure out how to convert earth data to numpy array or list
  #print(earth_data_clipped.toArray().getInfo())

  # Style parameters for Earth Engine data
  earth_data_style = {
    "min": 0,
    "max": 3000,
    "palette": [ #list of colors
      "#000000", "#141414", "#292929", "#3D3D3D", "#525252", 
      "#666666", "#7B7B7B", "#8F8F8F", "#A4A4A4", "#B8B8B8", "#E8E8E8", "#FFFFFF"
    ],
    "opacity": 0.8 #transparency
  }

  # Get URL of tile layer created from the processed Earth Engine data
  map_id_dict = earth_data_clipped.getMapId(earth_data_style)
  #print(map_id_dict)

  # Want to get values at points
  # For a given point, take the most recent value
  # TODO: figure out how to (use reduce?) to get most recent values at points

  #map_id_dict = earth_data_filter_aoi.getMapId(earth_data_style)
  earth_data_url = map_id_dict["tile_fetcher"].url_format
  
  #return render(request, template, context)
  return earth_data_url

# Function to render a web map of earth engine data 
def render_earth_data(request):
  # Define template to render
  template = "getdata/earthengine.html"

  # Get google earth data
  data_url = get_earth_data(data_name=ELEVATION_DATA_NAME, sample_points=test_sampling_points)

  # Reverse point data for use with folium
  sampling_points_yx = map(lambda coords: coords[::-1], test_sampling_points["coordinates"])

  # Create dictionary of spatial data to add to map
  map_data = {
    "point": sampling_points_yx,
    #"line": list(sampling_points_yx),
    "raster": data_url,
  }

  # Create Folium map from the google earth data
  folium_map = create_map(
    map_data_dict=map_data,
    centroid=[32.31, -110.71])
  
  # Context object to render
  context = {
    "data_name": ELEVATION_DATA_NAME,
    "aoi": test_sampling_points,
    "map": folium_map,
    }

  return render(request, template, context)


# Specify the url we redirect the user to after they are logged in
# login_required will redirect the user to the login page (specifed at LOGIN_URL in settings)
# Note that the code in getStravaData does not execute until after the user is logged in and visits the page again
# The default redirect URL after the user is logged in is specified in settings.SOCIAL_AUTH_LOGIN_REDIRECT_URL
@login_required
def render_strava_data(request):
  # Define template to render
  template = "getdata/index.html"

  # Get the current user from the request
  user = request.user

  # For testing
  current_athlete = "no athlete"
  athlete_name = "NA"
  context = {
    "current_athlete": current_athlete,
    "athlete_name": athlete_name,
  }

  # Check if the user is authenticated (this may be unnecessary given the login_required decorator)
  if user.is_authenticated:

    try:
      strava_access_token = get_token(user, "strava")
    
      # Create new client instance with the access token we generated
      client = Client(access_token = strava_access_token)

      # Get test data about athlete
      current_athlete = client.get_athlete()
      athlete_name = current_athlete.firstname + " " + current_athlete.lastname
      #routes = client.get_routes(limit = 10)
      # Get all routes from Strava activity
      routes = client.get_routes() # TODO: Figure out why this is only getting two records

      # List of route objects
      route_list = []

      #Extract routes from list and create new route objects to save in DB
      for route in routes:
        # Have to decode the google polyline format using the 'polyline' package
        # And then create a new LineString object using the resulting list of coordinates
        lat_long = polyline.decode(route.map.summary_polyline)
        # Then have to reverse the (lat, long) coordinate format to get (long, lat) format for LineString 
        # Note: Folium and GeoDjango appear to have opposite coordinate format requirements
        # Folium wants data in (lat, long) format,
        # and GeoDjango spatial objects are created from (long, lat) format
        long_lat = list(map(lambda coords: coords[::-1], lat_long))
        
        # Check if activity object already exists
        user_filter = Activity.objects.filter(user_id = user.id)
        route_filter = user_filter.filter(activity_id = route.id)
        if(not route_filter.exists()):
          # Create new route object for each route
          current_route = Activity.objects.create_activity(
            user=user,
            activity=str(route.id),
            start_date=timezone.now(), #TODO: See if there is a way to get actual date of run from strava -> seems to be missing from stravalib route object
            created_date=timezone.now(),
            line=LineString(long_lat), # Convert lat_long data to GeoDjango LineString format
          )
          route_list.append(current_route)
          current_route.save() # Save the object in the database

        else:
          print("Route already exists")

      # Generate points along routes at specified distance
      #interpolate_points(ELEVATION_EXTRACTION_RESOLUTION)

      # Get a recent route for testing
      if(len(route_list) > 0):
        recent_route = route_list[0]

        # Convert (long, lat) data back to (lat, long) for folium
        route_yx = list(map(lambda coords: coords[::-1], recent_route.line))
        
        # Plot route on map
        centroid = [
            np.mean([coord[0] for coord in route_yx]), 
            np.mean([coord[1] for coord in route_yx])
        ]

        context = {
          "current_athlete": current_athlete,
          "athlete_name": athlete_name,
          "routes": routes,
          #"map_test": figure,
        }

      else:
        # Get latest route
        route = [Activity.objects.filter(user_id = user.id).order_by("-date")[0]]
        context = {
          "current_athlete": current_athlete,
          "athlete_name": athlete_name,
          "routes": route,
        }
    
    except UserSocialAuth.DoesNotExist:
        #strava_login = None
        current_athelete = "no strava athlete account"
  
  # If user has not authenticated with strava
  else:
    context = {
      "current_athlete": current_athlete,
      "athlete_name": athlete_name,
    }

  return render(request, template, context)

@login_required #take out since this is called from login required already
def prep_strava(request): #pass in request.user?
  template = "getdata/index.html" #remove
  user = request.user
  if user.is_authenticated:
    strava_access_token = get_token(user, "strava")
    client = Client(access_token = strava_access_token)
    #current_athlete = client.get_athlete()
    #athlete_name = current_athlete.firstname + " " + current_athlete.lastname
    return client
  else:
    context = {
      "current_athlete": current_athlete,
      "athlete_name": athlete_name,
    }
  return render(request, template, context) #can return "not authenticated"


#Lots of repeat in this. Can we make this more efficient with better programming OR class based views?
@login_required
def get_stream(request, activity, streamtype):
  #call prep_strava, which will throw an exception if the user isn't authenticated
  client = prep_strava(request)
  #get requested stream
  desired_stream = client.get_activity_streams(activity_id = activity, types = streamtype, resolution ='medium' )
  return desired_stream
