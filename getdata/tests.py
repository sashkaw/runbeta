# Imports
import os
import datetime
import requests
from datetime import datetime
from dotenv import load_dotenv
from unittest import mock, skip
import stravalib.client as stravacli
from stravalib.model import Athlete

from django.test import TestCase, override_settings
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
import django.test.client as djangotestcli

from social_django.models import UserSocialAuth
from social_django.views import get_session_timeout

from .views import *
from .models import Activity

# Create your tests here.

# Load login info for test user
load_dotenv()
TEST_USER_NAME = os.getenv("TEST_USER_NAME")
TEST_USER_PASSWORD= os.getenv("TEST_USER_PASSWORD")
TEST_RASTER_URL = os.getenv("TEST_RASTER_URL")
TEST_TILE_LAYER_REGEX = os.getenv("TEST_TILE_LAYER_REGEX")

# Helper function to create new users for testing
def create_user():
  new_user = User.objects.create(username='testuser', password='12345', is_active=True, is_staff=True, is_superuser=True) 
  new_user.set_password('hello') 
  new_user.save() 
  new_user = authenticate(username='testuser', password='hello') 
  #login = self.client.login(username='testuser', password='hello') 
  #self.assertTrue(login)
  return new_user


class CreateMap(TestCase):
  """
  Test that folium maps can be created
  """
  # Initialize test data
  # TODO: Fix views so that create_map takes in geojson objects instead of just coordinates?
  def setUp(self):
    self.test_centroid = [32.31, -110.71]
    self.test_map_data = {
      "point":
      [
        [-110.72, 32.30],
        [-110.69, 32.31],
        [-110.67, 32.29],
      ],
      "line":
      [
        [-110.71, 32.31],
        [-110.68, 32.32],
        [-110.66, 32.30],
      ],
      "polygon":
      [
        [-110.79, 32.24],
        [-110.69, 32.24],
        [-110.69, 32.33],
        [-110.79, 32.33],
        [-110.79, 32.24],
      ],
      "raster": TEST_RASTER_URL,
    }

  def test_create_map(self):
    test_map = create_map(map_data_dict=self.test_map_data, centroid=self.test_centroid)
    # Check that rendered map contains a leaflet map
    self.assertRegex(test_map, "L.map") 
    # Check that map contains correct centroid
    self.assertRegex(test_map, "center: \[32.31, -110.71\]")
    # Check that map contains correct point markers
    self.assertRegex(test_map, "L.marker\((\s+)\[-110.72, 32.3]")
    self.assertRegex(test_map, "L.marker\((\s+)\[-110.69, 32.31]")
    self.assertRegex(test_map, "L.marker\((\s+)\[-110.67, 32.29]")
    # Check that map contains correct line layer
    self.assertRegex(test_map,  "L\.polyline\((\s+)\[\[-110.71, 32.31\], \[-110.68, 32.32\], \[-110.66, 32.3\]\]")
    # Check that map contains correct polygon layer
    self.assertRegex(test_map, "L\.polygon\((\s+)\[\[-110.79, 32.24\], \[-110.69, 32.24\], \[-110.69, 32.33\], \[-110.79, 32.33\], \[-110.79, 32.24\]\]")
    # Check that map contains correct tile layer
    self.assertRegex(test_map, TEST_TILE_LAYER_REGEX)

class AuthStrava(TestCase):
  """
  Test that user can authenticate with strava
  """

  # Load test user fixtures
  fixtures = ["fixtures/user.json", "fixtures/socialauth.json"]
  @skip("Writing tests...")
  # Initialize test client and login the test user
  def setUp(self):
    self.client = djangotestcli.Client()
    self.response = self.client.login(username=TEST_USER_NAME, password=TEST_USER_PASSWORD)

  # Check that strava auth token can be returned / refreshed
  # Function will return UserSocialAuth error if user is not authenticated with strava
  # TODO: Add error checking within the function?
  @skip("Writing tests...")
  def test_get_token(self):
    # Get user object for tests
    test_user = User.objects.get(pk=3)
    test_provider = "strava"
    # Get token
    token = get_token(user=test_user, provider=test_provider)
    self.assertIsInstance(token, str) # Check that output is a string
    self.assertGreater(len(token), 0) # Check that output has length greater than zero

  # Check that prep_strava returns a valid client object for authenticated strava user
  @skip("Writing tests...")
  def test_prep_strava(self):
    # Get user object for tests
    test_user = User.objects.get(pk=3)
    test_client = prep_strava(test_user)
    self.assertIsInstance(test_client, stravacli.Client)
    
  # Check that "no user" is returned when user object is not authenticated with strava
  @skip("Writing tests...")
  def test_prep_strava_no_user(self):
    test_user = create_user()
    test_client = prep_strava(test_user)
    self.assertEqual(test_client, "no user")

    
class RenderStrava(TestCase):
  """
  Test that strava data is being fetched and rendered for an authenticated user
  """

  # Load test user fixtures
  fixtures = ["fixtures/user.json", "fixtures/socialauth.json"]

  # Initialize test client and login the test user
  @skip("Writing tests...")
  def setUp(self):
    # Initalize django test client, strava client
    self.client = djangotestcli.Client()
    self.test_user = User.objects.get(pk=3)
    self.strava_client = prep_strava(self.test_user)
    # Log in test user
    self.response = self.client.login(username=TEST_USER_NAME, password=TEST_USER_PASSWORD)

  @skip("Writing tests...")
  # Check that user strava data is being fetched and rendered
  def test_render_strava(self):
    self.response = self.client.get(reverse('getdata:getdata-strava'))
    self.assertTrue(200, self.response.status_code)
    self.assertTemplateUsed(self.response, 'getdata/index.html')
    # Check that athlete is of correct type
    self.assertIsInstance(self.response.context["current_athlete"], Athlete) 
    # Check that there is at least one activity
    self.assertGreater(len(self.response.context["activities"]), 0)
    # Check that rendered map contains a leaflet map
    self.assertRegex(self.response.context["map"], "L.map") 
  
  # Check that strava activities can be fetched for an authenticated user
  @skip("Writing tests...")
  def test_get_activities(self):
    date_start = datetime(2022, 1, 1)
    date_end = datetime(2022, 11, 15)
    test_activities = get_strava_activities(self.test_user, self.strava_client, date_start, date_end, limit=None)
    print(test_activities)


"""
class GetEarthDataTests(TestCase):
  @skip("Writing tests...")
  def test_get_earth_data_url(self):
   
   #Test that url returned from get_earth_data() returns a valid response code

    test_aoi = {
      "type": "LineString",
      "coordinates": 
      [
          [-110.71, 32.31],
          [-110.68, 32.32],
          [-110.66, 32.30]
      ]
    }

    # Call the function on elevation data and the test area of interest geojson defined above
    #data_url = get_earth_data(data_name="USGS/3DEP/1m", area_of_interest=test_aoi)
    #print(data_url)
    # Make a request to the URL
    #response = requests.get(data_url)
    #self.assertEqual(response.status_code, 200)

#def create_test_route(route_text):
  
  #Create a user with the given `user_text` and created the
  #given number of `days` offset to now (negative for users created
  #in the past, positive for user that have yet to be created).
  
  #time = timezone.now() + datetime.timedelta(days=days)
  #return Route.objects.create_route(user_text = user_text, creation_date = time)

#class UserModelTests(TestCase):

  #def test_no_users(self):
    
    #If no users exist, display a message
  
    #response = self.client.get(reverse("authstrava:index"))
    #self.assertEqual(response.status_code, 200)
    #self.assertContains(response, "No users are available.")
    #self.assertQuerysetEqual(response.context["latest_user_list"], [])"""
