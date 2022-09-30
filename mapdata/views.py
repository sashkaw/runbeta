# django imports
from re import T
from curses.ascii import HT
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import TemplateView
from django.urls import reverse
from django.views import generic
from django.utils import timezone
#from django.template import loader
#from django.http import Http404
from django.urls import reverse

# package imports
import os
from dotenv import load_dotenv
import pandas as pd
import folium
from folium import plugins
import ee

from .models import User, Route

# Create your views here.

# Function to autenticate with Google so we can use the Google Earth Engine API
def gee_auth():
    # Trigger GEE authentication flow
    #manual
    #ee.Authenticate()
    #ee.Initialize()

    # Automatic using service account (tutorial: https://developers.google.com/earth-engine/guides/service_account)
    # Get path to secrets file
    load_dotenv()
    SECRETS_PATH = os.getenv('SECRETS_PATH')
    JSON_NAME = os.getenv("JSON_NAME")

    # Load secrets .env
    load_dotenv(f"{SECRETS_PATH}/.env")
    # Get name of service account
    EE_SERVICE_ACCOUNT = os.getenv("EARTH_ENGINE_SERVICE_ACCOUNT")

    # service_account = EE_SERVICE_ACCOUNT
    # Authenticate
    credentials = ee.ServiceAccountCredentials(EE_SERVICE_ACCOUNT, f"{SECRETS_PATH}/{JSON_NAME}")
    ee.Initialize(credentials)


# Run authentication for GEE 
# Note: key must be accessible, 
# Service account email must be registered, 
# And GEE API must be enabled for cloud project)
gee_auth() 

# Function to display test message on home page (index.html)
class IndexView(generic.ListView):
  template_name = "mapdata/index.html"
  context_object_name = "latest_user_list"

  def get_queryset(self):
    # Return last 5 created users (not including ones published in the future)
    return User.objects.filter(
      creation_date__lte=timezone.now()
      ).order_by("-creation_date")[:5]

# Function to display web map of google earth engine data
# Script must have gone through Google authentication step (gee_auth()) for this to work
# This creates a web map using the Folium python package
# Folium is a python package for visualizing geospatial data based on the leaflet.js open-source javascript library for creating web maps
class FoliumView(TemplateView):
    template_name = "mapdata/map.html"

    # Method for displaying earth engine data with folium
    def get_context_data(self, **kwargs):
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
        elevationPima = elevation_data.filterBounds(pimaCounty)

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

        # Return the map object
        return {"map": figure}