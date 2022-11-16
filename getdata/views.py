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
from django.contrib.auth.forms import AdminPasswordChangeForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth import update_session_auth_hash, login, authenticate
from django.contrib import messages
from django.contrib.gis.geos import LineString, Point, MultiPoint
from django.core.serializers import serialize
from django.db import connection
from datetime import datetime

# Custom models
from .models import Activity

# Package imports
from social_django.models import UserSocialAuth
from social_django.utils import load_strategy
import os
import time
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
ACTIVITY_STREAM_TYPES = [
  "time", 
  "latlng", 
  "distance", 
  "altitude", 
  "velocity_smooth",
  "heartrate", 
  "cadence", 
  "watts", 
  "temp", 
  "moving", 
  "grade_smooth"
  ]

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
  fg=folium.FeatureGroup(name='Strava activity', show=False)
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

# View to test that app can connect successfully to Google Earth Engine
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
def get_earth_data(data_name, sample_points, get_url=False):

  # Get an object to work with
  #recent_activity = Activity.objects.get(pk=1) # For testing

  # Convert data to geojson
  #sample_points_json = json.loads(sample_points.geojson)

  # Create earth engine geometry from sample_points
  sample_points_ee = ee.Geometry(sample_points)
  #print(sample_points_ee.getInfo())

  # Get elevation data
  # Note: the USGS 3D Elevation Profile data seems to be the best
  # Elevation data that Google Earth Engine offers (at 1m resolution)
  # Extract the most recent image from the collection
  earth_data = ee.ImageCollection(data_name)

  # Sample maximum value for earth data at points of interest
  # TODO: Figure out how to get most recent data at points of interest?
  #earth_data_sample = earth_data_max.sample(sample_points_ee)
  earth_data_sampled = earth_data.max().sample(sample_points_ee, 1)
  earth_data_sampled_list = earth_data_sampled.aggregate_array("elevation").getInfo() # TODO: See if better way to do this? Maybe not -> https://gis.stackexchange.com/questions/363022/reasons-to-use-plain-synchronous-getinfo-in-gee

  # Get tile layer of the extracted data if (get_url == True)
  if(get_url == True):
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
    map_id_dict = earth_data_sampled.getMapId(earth_data_style)
    earth_data_url = map_id_dict["tile_fetcher"].url_format

    output_data = {
      "data_url": earth_data_url,
      "data_list": earth_data_sampled_list
    }

  else:
    output_data = {
      "data_list": earth_data_sampled_list
    }

  return output_data 

# Function to render a web map of earth engine data (mostly for debugging / testing currently)
def render_earth_data(request):
  # Define template to render
  template = "getdata/earthengine.html"

  # Get google earth data
  earth_dict = get_earth_data(data_name=ELEVATION_DATA_NAME, sample_points=test_sampling_points, get_url=True)
  data_url = earth_dict["data_url"]
  #data_list = earth_dict["data_list"]

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
      
      # Get all strava activities
      # NOTE: Need to specify SOCIAL_AUTH_STRAVA_SCOPE = ['activity:read_all'] in settings.py for this to work
      # TODO: Figure out best method for only getting new data as needed (data filter since last activity 'date_created'?)
      activities = client.get_activities(
        before=datetime(2022, 11, 15),
        after=datetime(2022, 10, 15),
        limit=2)

      # List of activity objects
      activity_list = []

      #Extract activities from list and create new activity objects to save in DB
      for activity in activities:
        # Have to decode the google polyline format using the 'polyline' package
        # And then create a new LineString object using the resulting list of coordinates
        lat_long = polyline.decode(activity.map.summary_polyline)
        # Then have to reverse the (lat, long) coordinate format to get (long, lat) format for LineString 
        # Note: Folium and GeoDjango appear to have opposite coordinate format requirements
        # Folium wants data in (lat, long) format,
        # and GeoDjango spatial objects are created from (long, lat) format
        long_lat = list(map(lambda coords: coords[::-1], lat_long))
        
        # Check if activity object already exists
        check_user = Activity.objects.filter(user_id = user.id)
        check_activity = check_user.filter(activity_id = activity.id)
        if(not check_activity.exists()):
          
          # Get activity_stream data for that activity
          #activity_stream = client.get_activity_streams(activity_id = activity.id, types = ACTIVITY_STREAM_TYPES, resolution ='medium') 
          #print(activity_stream)
          #print(type(activity.id))
          #print("\n")
          #print(activity)
          #print("\n")
          
          # Create new activity object for each activity
          current_activity = Activity.objects.create_activity(
            user=user,
            activity=str(activity.id),
            start_date=activity.start_date, 
            created_date=timezone.now(),
            line=LineString(long_lat), # Convert lat_long data to GeoDjango LineString format
          )
          activity_list.append(current_activity)
          current_activity.save() # Save the object in the database

        else:
          print("Activity already exists")

      # Get a recent activity for testing
      if(len(activity_list) > 0):
        recent_activity = activity_list[0]

      else:
        # Get latest route
        recent_activity = Activity.objects.filter(user_id = user.id).order_by("-start_date")[0]

      # Get activity_stream data for the recent activity (probably will move this up to the main loop above, just separating for testing currently)
      activity_stream = client.get_activity_streams(activity_id = activity.id, types = ACTIVITY_STREAM_TYPES, resolution ='medium') 
      stream_latlng = activity_stream.get("latlng").data
      # Get every 60th element (because data is sampled at roughly one second, this should get a data point for every minute)
      stream_sample = stream_latlng[::60]
      # Reverse coordinates for earth engine (earth engine wants data in longlat format)
      # and create geometry object for earth engine from coordinates
      sample_points = MultiPoint(list(map(lambda lnglat: Point(lnglat[::-1]), stream_sample)))
      # Convert to geojson format (the .geojson member is a string, so we use json_loads to convert the object to a dictionary)
      sample_coords = json.loads(sample_points.geojson)
      
      # Save activity stream data to database
      recent_activity.latlng = sample_points # TODO: Decide if we want to get full data or just sampled points
      recent_activity.save()
      #print(type(sample_points))

      # Get google earth data using the sampled points geojson
      earth_dict = get_earth_data(data_name=ELEVATION_DATA_NAME, sample_points=sample_coords)
      data_list = earth_dict["data_list"]
      #print(data_list)

      # Save elevation data in the database
      recent_activity.elevation = data_list
      recent_activity.save()

      # Convert (long, lat) data back to (lat, long) for folium
      activity_yx = list(map(lambda coords: coords[::-1], recent_activity.line))
      
      # Create centroid for map
      centroid = [
          np.mean([coord[0] for coord in activity_yx]), 
          np.mean([coord[1] for coord in activity_yx])
      ]
    
      # Create dictionary of spatial data to add to map
      map_data = {
        "point": activity_yx,
        "line": list(activity_yx),
      }

      # Create Folium map from the strava data
      folium_map = create_map(
        map_data_dict=map_data,
        centroid=centroid)

      context = {
        "current_athlete": current_athlete,
        "athlete_name": athlete_name,
        "activities": activities,
        "map": folium_map,
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

@login_required
def prep_strava(request):
  template = "getdata/index.html"
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
  return render(request, template, context)


#Lots of repeat in this. Can we make this more efficient with better programming OR class based views?
@login_required
def get_stream(request, activity, streamtype):
  #call prep_strava, which will throw an exception if the user isn't authenticated
  client = prep_strava(request)
  #get requested stream
  desired_stream = client.get_activity_streams(activity_id = activity, types = streamtype, resolution ='medium' )
  return desired_stream
