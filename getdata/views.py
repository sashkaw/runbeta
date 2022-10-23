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
#from django.template import loader
#from django.http import Http404
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AdminPasswordChangeForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth import update_session_auth_hash, login, authenticate
from django.contrib import messages
from django.contrib.gis.geos import LineString
#from django.contrib.gis.db.models.functions import Envelope, Intersection
from django.core.serializers import serialize

# Custom models
from .models import Route, Elevation

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
import polyline
from stravalib.client import Client

#import dill
import os
#from os.path import exists
from dotenv import load_dotenv
#import pandas as pd
#import matplotlib.pyplot as plt
#import numpy as np
#from scipy import optimize
#from IPython.display import Image
#import folium
import ee
import json
#%matplotlib inline


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

# Below code is just to check that we can get data from strava when authenticated with strava using django social auth
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

# View to test that app can connect successfull to Google Earth Engine
def getEarthData(request):
  template = "getdata/earthengine.html"

  # Get polyline of route

  # Get bounding box of polyline

  # Somehow download only the google earth data for a terrain dataset for that bounding box

  # Add points every 'x' meters to the polyline?

  # Intersect the clipped google earth data with the polyline

  # Extract values from intersected data to an array corresponding to each point in the route?

  # Create figure object so we can plot things inside of it
  figure = folium.Figure() 

  # Create Folium basemap object
  m = folium.Map(
      location = [32.352343, -110.801944],
      zoom_start=12
  )

  # Add map to figure
  m.add_to(figure)

  # Get data of US counties so we can filter for the area of interest
  counties = ee.FeatureCollection("TIGER/2018/Counties")
  pimaCounty = counties.filter(ee.Filter.eq("NAME", "Pima"))
  #print(pimaCounty.first().getInfo())

  # Get elevation data
  # Note: the USGS 3D Elevation Profile data seems to be the best
  # Elevation data that Google Earth Engine offers (at 1m resolution)
  elevation_data = ee.ImageCollection('USGS/3DEP/1m')

  # Get NAIP data (RGB and near infrared? -> may come in handy for image classification)
  #terrainData = ee.ImageCollection('USDA/NAIP/DOQQ').filter(ee.Filter.date('2017-01-01', '2018-12-31'))
  #print(terrainData.getInfo())
  #trueColor = terrainData.select(['R', 'G', 'B'])

  # Extract terrain data for area of interest
  #terrainPima = trueColor.filterBounds(pimaCounty)
  #print(terrainPima.first().getInfo())
  elevation_data = elevation_data.filterBounds(pimaCounty)

  # Style for elevation data
  elevationStyle = {
    "min": 0,
    "max": 3000,
    "palette": [ #list of colors
      "#000000", "#141414", "#292929", "#3D3D3D", "#525252", 
      "#666666", "#7B7B7B", "#8F8F8F", "#A4A4A4", "#B8B8B8", "#E8E8E8", "#FFFFFF"
    ],
    "opacity": 0.8 #transparency
  }

  # Style for NAIP DATA
  #trueColorVis = {
  #    "min": 0.0,
  #    "max": 255.0,
  #}

  # Add map to folium map
  #map_id_dict = ee.Image(terrainPima.first()).getMapId(trueColorVis)
  #map_id_dict = terrainPima.getMapId(trueColorVis)
  map_id_dict = elevationPima.getMapId(elevationStyle)
  #print(map_id_dict["tile_fetcher"].url_format)

  # Create Folium raster tile layer from elevation data and add it to the map we created above
  folium.raster_layers.TileLayer(
      #Get URL to the elevation data on Google Earth Engine
      tiles = map_id_dict["tile_fetcher"].url_format, 
      #tiles = "Stamen Terrain",
      attr = "Google Earth Engine",
      name = "3DEP",
      overlay = True,
      control = True,
  ).add_to(m)

  # Add layer control (to loggle layers on/off)
  m.add_child(folium.LayerControl())

  # Render the figure object
  figure.render()

  context = {
    "map": figure,
  }

  # Return the map object
  return render(request, template, context)

# Specify the url we redirect the user to after they are logged in
# login_required will redirect the user to the login page (specifed at LOGIN_URL in settings)
# Note that the code in getStravaData does not execute until after the user is logged in and visits the page again
# The default redirect URL after the user is logged in is specified in settings.SOCIAL_AUTH_LOGIN_REDIRECT_URL
@login_required
def getStravaData(request):
  template = "getdata/index.html"
  #template = "getdata/details.html"

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
      all_routes = client.get_routes(limit = 5)
      routes = client.get_routes(limit = 10)

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
        
        # Create new route object for each route
        current_route = Route.objects.create_route(
          user=user,
          route=str(route.id),
          date=timezone.now(),
          distance=route.distance,
          line=LineString(long_lat), # Convert lat_long data to GeoDjango LineString format
        )
        route_list.append(current_route)
        current_route.save() # Save the object in the database
    
      # Get a recent route for testing
      recent_route = route_list[0]
      
      # Convert (long, lat) data back to (lat, long) for folium
      route_yx = list(map(lambda coords: coords[::-1], recent_route.line))
      
      # Plot route on map
      centroid = [
          np.mean([coord[0] for coord in route_yx]), 
          np.mean([coord[1] for coord in route_yx])
      ]

      # Convert route data to geojson
      route_line = recent_route.line.geojson
      route_line = json.loads(route_line)
      #print(route_line)
      route_line_ee = ee.Geometry(route_line)
      #print(route_line_ee.getInfo())


      # Get bounding box for route data in string format containing geojson TODO: See if there is a better way to extract this data?
      route_bbox = recent_route.line.envelope.geojson
      # Convert the string to a geojson dictionary
      route_bbox = json.loads(route_bbox)
      # Convert route bounding box to GEE format
      #route_bbox_ee = ee.Feature(route_bbox) # Doesn't work for filterBounds()
      # Create GEE Geometry object from bounding box
      route_bbox_ee = ee.Geometry(route_bbox)

      # Get elevation data
      # Note: the USGS 3D Elevation Profile data seems to be the best
      # Elevation data that Google Earth Engine offers (at 1m resolution)
      # Extract the most recent image from the collection
      elevation_data = ee.ImageCollection('USGS/3DEP/1m')
      #elevation_data = elevation_data.limit(1, "system:time_start").first()
      #print(elevation_data)
      # Note: Google Earth Engine documentation states that GEE handles projections automatically
      #print(elevation_data.getInfo()) #Coordinate system: EPSG:26910
      #elevation_crs = elevation_data.first().projection().crs().getInfo()
      #elevation_crs = ee.Projection(elevation_crs)
      #print(elevation_crs)

      # Project route bounding box to elevation crs
      # Have to specify maxError or function will throw error
      #route_bbox_ee = route_bbox_ee.transform(proj=elevation_crs, maxError=1)

      # Get NAIP data (RGB and near infrared? -> may come in handy for image classification)
      #terrainData = ee.ImageCollection('USDA/NAIP/DOQQ').filter(ee.Filter.date('2017-01-01', '2018-12-31'))
      #print(terrainData.getInfo())
      #trueColor = terrainData.select(['R', 'G', 'B'])

      # Extract terrain data for area of interest
      route_elevation = elevation_data.filterBounds(route_bbox_ee) # For image collection 
      # NOTE: image collection seems to be easier to work with and map with folium compared to image...
      #route_elevation = elevation_data.clip(route_bbox_ee)
      #route_elevation = elevation_data
      #print(type(route_elevation))
      #elevation_values = route_elevation.sample(region=route_line_ee, scale = 10) #TODO: Fix this to extract values from line
      # Add sampling at set regions?
      #elevation_values = elevation_data.getRegion(geometry=route_line, scale=10) #Outputs (id, lon, lat, time) (for image collection)
      #print(elevation_values.getInfo())

      # Add layer control (to loggle layers on/off)
      #m.add_child(folium.LayerControl())

      # Create test web map of route data
      figure = folium.Figure()
      m = folium.Map(
            location=centroid, 
            zoom_start=12,
            tiles="Stamen Terrain"
          )
        
      m.add_to(figure)

       # Style for elevation data
      elevation_style = {
        "min": 0,
        "max": 3000,
        "palette": [ #list of colors
          "#000000", "#141414", "#292929", "#3D3D3D", "#525252", 
          "#666666", "#7B7B7B", "#8F8F8F", "#A4A4A4", "#B8B8B8", "#E8E8E8", "#FFFFFF"
          #"845EC2", "#D65DB1", "#FF6F91", "#FF9671", "#FFC75F", "#F9F871"
          #'#fff7ec','#fee8c8','#fdd49e','#fdbb84','#fc8d59','#ef6548','#d7301f','#b30000','#7f0000'
        ],
        "opacity": 1 #transparency
      }

      # Style for NAIP DATA
      #trueColorVis = {
      #    "min": 0.0,
      #    "max": 255.0,
      #}

      # Add map to folium map
      map_id_dict = route_elevation.getMapId(elevation_style)
      #map_id_dict = elevation_values.getMapId(elevation_style)
      #print(map_id_dict["tile_fetcher"].url_format)

      # Create Folium raster tile layer from elevation data and add it to the map we created above
      folium.raster_layers.TileLayer(
          #Get URL to the elevation data on Google Earth Engine
          tiles=map_id_dict["tile_fetcher"].url_format, 
          #tiles="Stamen Terrain",
          attr="Google Earth Engine",
          name="3DEP",
          overlay=True,
          control=True,
      ).add_to(m)

      # Add bounding box of route to map
      folium.GeoJson(route_bbox).add_to(m)

      # Create polyline from route data and add it to the folium map
      folium.PolyLine(route_yx, color='red', popup=f"Route ID: {recent_route.route_id}", control=True).add_to(m)
      
      # add toggle on/off for layer visibility
      folium.LayerControl().add_to(m)

      #display(m)
      figure.render()

      context = {
        "current_athlete": current_athlete,
        "athlete_name": athlete_name,
        "routes": routes,
        "map_test": figure,
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

    

  

