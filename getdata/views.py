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
from folium import plugins
import polyline
from stravalib.client import Client


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
        current_route = Route.objects.create_route(
          user=user, 
          route=str(route.id),
          date=timezone.now(),
          distance=route.distance,
          # Have to decode the google polyline format using the 'polyline' package
          # And then create a new LineString object using the resulting list of coordinates
          line=LineString(polyline.decode(route.map.summary_polyline))
        )
        route_list.append(current_route)
        current_route.save() # Save the object in the database
    
      recent_route = route_list[0]

      # plot route on map
      centroid = [
          np.mean([coord[0] for coord in recent_route.line]), 
          np.mean([coord[1] for coord in recent_route.line])
      ]

      #create test web map of route data
      figure = folium.Figure()
      m = folium.Map(
            location=centroid, 
            zoom_start=12,
            tiles="Stamen Terrain"
          )
        
      m.add_to(figure)

      # create polyline from route data and add it to the folium map
      folium.PolyLine(recent_route.line, color='red').add_to(m)
      
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

    

  

