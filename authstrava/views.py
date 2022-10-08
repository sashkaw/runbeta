# django imports
from multiprocessing import context
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
from .models import User, Route

# package imports
import os
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import folium
from folium import plugins
import polyline
from stravalib.client import Client
client = Client()

#get strava user secrets from .env file
load_dotenv("../.env")
STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID') # Instead of your actual secret key
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
TEST_ROUTE_ID = os.getenv("TEST_ROUTE_ID") #get one route id just for testing displaying web map

def authURL(request):
  template = "authstrava/authurl.html"
  #context =
  #template = loader.get_template('polls/index.html')

  # get authorization url for first time user manual authorization for access 
  # to their strava account
  auth_url = client.authorization_url(client_id=STRAVA_CLIENT_ID, 
        redirect_uri="http://127.0.0.1:8000/authstrava/authtoken/", # for local development
        scope=['read_all','profile:read_all','activity:read_all'])
  
  context = {
    "auth_url": auth_url,
  }

  return HttpResponse(render(request, template, context))


def authToken(request):
  template = "authstrava/authtoken.html"

  #get code from the authorization link 
  strava_client_code = request.GET.get("code")
  
  #exchange code for access token
  access_token = client.exchange_code_for_token(
    client_id = STRAVA_CLIENT_ID, 
    client_secret = STRAVA_CLIENT_SECRET, 
    code = strava_client_code
  )

  # TODO: save access token in DB here

  # get test data about athlete
  current_athlete = client.get_athlete()
  athlete_name = current_athlete.firstname + " " + current_athlete.lastname
  all_routes = client.get_routes(limit = 5)
  route_test = client.get_route(TEST_ROUTE_ID) # just for testing
  route_polyline = polyline.decode(route_test.map.summary_polyline) # have to decode the google polyline format using the 'polyline' package

  # plot route on map
  centroid = [
      np.mean([coord[0] for coord in route_polyline]), 
      np.mean([coord[1] for coord in route_polyline])
  ]

  #create test web map of route data
  figure = folium.Figure()
  m = folium.Map(
        location = centroid, 
        zoom_start=12,
        tiles = "Stamen Terrain")
    
  m.add_to(figure)

  # create polyline from route data and add it to the folium map
  folium.PolyLine(route_polyline, color='red').add_to(m)
  
  # add toggle on/off for layer visibility
  folium.LayerControl().add_to(m)

  #display(m)
  figure.render()

  context = {
    "auth_token": access_token,
    "current_athlete": current_athlete,
    "user_name": athlete_name,
    "routes": all_routes,
    "route_test" : route_test,
    "map_test" : figure,
  }

  return HttpResponse(render(request, template, context))



# Function to display test message on home page (index.html)
class IndexView(generic.ListView):
  template_name = "authstrava/index.html"
  context_object_name = "latest_user_list"

  def get_queryset(self):
    # Return last 5 created users (not including ones published in the future)
    return User.objects.filter(
      creation_date__lte=timezone.now()
      ).order_by("-creation_date")[:5]
