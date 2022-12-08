# Django imports
from multiprocessing import context
from re import T
from curses.ascii import HT
from tokenize import String
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import TemplateView
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AdminPasswordChangeForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib import messages
from django.contrib.gis.geos import LineString, Point, MultiPoint
from django.core.serializers import serialize
from django.db import connection

# Custom models
from .models import Activity

# Package imports
from social_django.models import UserSocialAuth
from social_django.utils import load_strategy
import os
import time
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import folium
from folium import Polygon, plugins
from folium.plugins import MarkerCluster
import polyline
from stravalib.client import Client
import ee
import json
from datetime import datetime

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

def get_token(user, provider):
  """
  Check if third party OAuth access token is still valid.
  If the token is invalid, refresh the token and return the new access token.
  Else return the valid current access token.

  Keyword arguments:
  user -- request.user object
  provider -- string name of provider (eg "strava")
  """
  social = user.social_auth.get(provider = provider)
  # the  ' - 10' is so that the token doesn't expire as we make the request 
  # if we check the token expiry right before it expires
  if (social.extra_data['auth_time'] + social.extra_data['expires'] - 10) <= int(time.time()):
      strategy = load_strategy() # Refresh token
      social.refresh_token(strategy)
  return social.extra_data['access_token']

def create_map(map_data_dict, centroid):
  """
  Create a Folium map object.
  
  Keyword arguments:
  map_data_dict -- dictionary of the form:
  {
    <data_type>: <data>, 
    <data_type>: <data>,
  }
  <data_type> -- One of "polygon" for vector polygon data, "line" for vector line data, "point" for vector point data, or "raster" for raster data
  <data> -- GEOS spatial data object (eg LineString, Point)

  centroid -- list of the form [latitude, longitude] for centering the Folium map (eg [32.31, -110.71])
  """
  
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

def get_earth_data(data_name, sample_points, get_url=False):
  """
  Get earth engine image collection data and sample raster values at points of interest.
  Return url to tile layer of extracted data if desired.

  Keyword arguments:
  data_name -- string name of earth engine data to retrieve
  sample_points -- geojson containing points at which to extract raster values
  get_url -- optional flag for whether to also return a tile layer url of the sampled data (default: False)
  """

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
# TODO: If decide to keep this function, update function to get parameters get_earth_data() from redirect to this view
test_sampling_points = {
      "type": "MultiPoint",
      "coordinates": 
      [
          [-110.71, 32.31],
          [-110.68, 32.32],
          [-110.66, 32.30]
      ]
    }
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

def prep_strava(current_user):
  """
  Get strava client object for the current user.

  Keyword arguments:
  current_user -- request.user (User model object)
  """
  if current_user.is_authenticated:
    try:
      strava_access_token = get_token(current_user, "strava")
      client = Client(access_token = strava_access_token)
      return client
    except UserSocialAuth.DoesNotExist:
        return "no user"
  else:
    return "not authenticated"

def extract_points(stream_data):
  """
  Extract lat long data from activity stream, sample the lat long data,
  convert to GEOS geometry, and extract geojson format.

  Keyword arguments:
  stream_data -- stravalib activity_stream object
  """
  # Get latlng data from the activity stream
  # Check if latlng key exists - some activities do not have latlng data
  if("latlng" in stream_data):
    #print("latlng exists")
    stream_latlng = stream_data.get("latlng").data
    # Get every 60th element (because data is sampled at roughly one second, this should get a data point for every minute)
    # stream_sample = stream_latlng[::60]
    # Reverse coordinates for earth engine (earth engine wants data in longlat format)
    # and create geometry object for earth engine from coordinates
    sample_points = MultiPoint(list(map(lambda lnglat: Point(lnglat[::-1]), stream_latlng)))
    # Convert to geojson format (the .geojson member is a string, so we use json_loads to convert the object to a dictionary)
    # so that we can pass the data to earth engine
    sample_json = json.loads(sample_points.geojson)

  else:
    sample_points = ""
    sample_json = ""

  point_dict = {
    "points": sample_points,
    "json": sample_json,
  }

  return point_dict

def get_strava_activities(user, client, date_start, date_end, limit=None):
  """
  Get strava activities for a given user ID and strava client object. 
  For each activity, get the activity stream data for that activity,
  extract longlat data from the activity stream, and extract 
  earth engine data for those points. Save all newly created objects in the database.
  Return a list of all the newly created objects. List will contain a string error message
  for a given activity if the activity already exists in the database.

  Keyword arguments:
  user -- request.user (User model object)
  client -- stravalib Client object
  date_start -- datetime object (e.g. of the form YYYY-MM-DD)
  date_end -- datetime object (e.g. of the form YYYY-MM-DD)
  limit -- integer number of maximum records to retrieve
  """

  # Handle optional limit argument and 
  # get activities for provided date range
  if(limit):
    activities = client.get_activities(before=date_end, after=date_start, limit=limit)
  else:
    activities = client.get_activities(before=date_end, after=date_start)

  # Create blank list of activity objects
  activity_list = []

  #Extract activities from list and create new activity objects to save in database
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
    # If the activity does not already exist, get activity stream data and 
    # earth engine data for the activity
    # and save in the database
    if(not check_activity.exists()):
      # Create new activity object for each activity
      current_activity = Activity.objects.create_activity(
        user=user,
        activity=str(activity.id),
        start_date=activity.start_date, 
        created_date=timezone.now(),
        line=LineString(long_lat), # Convert lat_long data to GeoDjango LineString format
      )
      
      # Get activity_stream data for the recent activity (probably will move this up to the main loop above, just separating for testing currently)
      activity_stream = client.get_activity_streams(activity_id = activity.id, types = ACTIVITY_STREAM_TYPES, resolution ='medium')
      get_streams(current_activity, activity_stream)

      # Get latlng data and create point objects and format coordinates for use with earth engine
      extracted_points = extract_points(activity_stream)
      extracted_multipoint = extracted_points.get("points")
      extracted_json = extracted_points.get("json")

      # Save activity stream data to database
      # TODO: Decide if we want to get full data or just sampled points?
      if(extracted_multipoint and extracted_json):
        # Store latlng data in database
        current_activity.latlng = extracted_points.get("points") 

        # Get google earth data using the sampled points geojson
        #earth_dict = get_earth_data(data_name=ELEVATION_DATA_NAME, sample_points=extracted_points.get("json"))
        # data_list = earth_dict["data_list"]
        # Save elevation data in the database
        #current_activity.elevation = data_list # altitude??

      # Add the current activities to a list (for if we want to access the activities without making more database calls)
      activity_list.append(current_activity)
      current_activity.save() # Save the object in the database
  return activity_list

def get_streams(activity, activity_stream):
  #activity.time = activity_stream.get("time").data
  activity.heartrate = activity_stream.get("heartrate").data
  #activity.cadence = activity_stream.get("cadence").data
  #activity.latlng = activity_stream.get("latlng") Already being done
  activity.distance = activity_stream.get("distance").data
  activity.altitude = activity_stream.get("altitude").data #Already being done??
  activity.velocity_smooth = activity_stream.get("velocity_smooth").data
  #activity.watts = activity_stream.get("watts").data
  activity.grade_smooth = activity_stream.get("grade_smooth").data
  #activity.temp = activity_stream.get("temp").data #my watch doesn't get this info
  #activity.moving = activity_stream.get("moving").data
  #activity.save()
  return activity

@login_required
def render_strava_data(request):
  """
  Get strava activity data, corresponding activity streams and sample earth engine raster data for the activity stream
  coordinates. Render Folium map of latest activity.
  
  Notes: 
  - login_required will redirect the user to the login page (specifed at LOGIN_URL in settings)
  - The default redirect URL after the user is logged in is specified in settings.SOCIAL_AUTH_LOGIN_REDIRECT_URL

  Keyword arguments:
  request -- Django HttpRequest object
  """

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

  # Get strava Client object
  client = prep_strava(user)

  # If client object is valid, get strava and earth engine data
  if(client != "no user" and client != "not authenticated"):
    # Get test data about athlete
    current_athlete = client.get_athlete()
    athlete_name = current_athlete.firstname + " " + current_athlete.lastname
    
    # Get activities and corresponding activity streams and sampled earth engine data for activity stream coordinates
    # TODO: Figure out best method for only getting new data as needed (date filter since last activity date_start or date_created?)
    # TODO: Add form functionality to select dates from a dropdown menu and 
    # redirect the output to a dashboard of the queried data
    # Get activities, 
    activity_list = get_strava_activities(
      user=user, 
      client=client, 
      date_start = datetime(2022, 1, 1), 
      date_end = timezone.now(),
      limit=5 # Function will take much longer without a limit -> TODO: See if this could be done in background? Or just add progress bar?
      )

    # Get a recent activity for testing
    if(len(activity_list) > 0):
      recent_activity = activity_list[0]

    # If there are no activities in the activity_list 
    # (eg the activities that were queried already exist in the database)
    else:
      # Get latest activity
      recent_activity = Activity.objects.filter(user_id = user.id).order_by("-start_date")[0]

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
      "activities": activity_list,
      "map": folium_map,
    }

  # Else if problem with strava client authentication
  else:
    context = {
      "current_athlete": current_athlete,
      "athlete_name": athlete_name,
    }

  return render(request, template, context) #can return "not authenticated"
