# Imports
import os
import datetime
import requests
from datetime import datetime
from dotenv import load_dotenv
from unittest import mock, skip
import stravalib.client as stravacli
from stravalib.model import Athlete, Activity

from django.test import TestCase, override_settings
from django.utils import timezone
from django.urls import reverse
from django.contrib.gis.geos import LineString, Point, MultiPoint
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
import django.test.client as djangotestcli


from social_django.models import UserSocialAuth
from social_django.views import get_session_timeout

from .views import *
from .models import Activity

# Load login info for test user
load_dotenv()
TEST_USER_NAME = os.getenv("TEST_USER_NAME")
TEST_USER_PASSWORD= os.getenv("TEST_USER_PASSWORD")
TEST_RASTER_URL = os.getenv("TEST_RASTER_URL")
TEST_TILE_LAYER_REGEX = os.getenv("TEST_TILE_LAYER_REGEX")

# Create your tests here.

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
  #@skip("Writing tests...")
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

  #@skip("Writing tests...")
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
  # Initialize test client and login the test user
  #@skip("Writing tests...")
  def setUp(self):
    self.client = djangotestcli.Client()
    self.response = self.client.login(username=TEST_USER_NAME, password=TEST_USER_PASSWORD)

  # Check that strava auth token can be returned / refreshed
  # Function will return UserSocialAuth error if user is not authenticated with strava
  # TODO: Add error checking within the function?
  #@skip("Writing tests...")
  def test_get_token(self):
    # Get user object for tests
    test_user = User.objects.get(pk=3)
    test_provider = "strava"
    # Get token
    token = get_token(user=test_user, provider=test_provider)
    self.assertIsInstance(token, str) # Check that output is a string
    self.assertGreater(len(token), 0) # Check that output has length greater than zero

  # Check that prep_strava returns a valid client object for authenticated strava user
  #@skip("Writing tests...")
  def test_prep_strava(self):
    # Get user object for tests
    test_user = User.objects.get(pk=3)
    test_client = prep_strava(test_user)
    self.assertIsInstance(test_client, stravacli.Client)

  # Check that "no user" is returned when user object is not authenticated with strava
  #@skip("Writing tests...")
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
  #@skip("Writing tests...")
  def setUp(self):
    # Initalize django test client, strava client
    self.client = djangotestcli.Client()
    self.test_user = User.objects.get(pk=3)
    self.strava_client = prep_strava(self.test_user)
    # Log in test user
    self.response = self.client.login(username=TEST_USER_NAME, password=TEST_USER_PASSWORD)
    # Set up dates for test queries
    self.date_start = datetime(2022, 11, 1)
    self.date_end = datetime(2022, 11, 15)

  # Check that user strava data is being fetched and rendered
  # Note: several times calling get_strava_activities via this test resulted in 
  # an error `stravalib.exc.Fault: 500 Server Error: Internal Server Error [error: None]`
  # Potential TODO: Fix functions so that server errors are handled within the functions?
  #@skip("Writing tests...")
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
  #@skip("Writing tests...")
  def test_get_activities(self):
    test_activities = get_strava_activities(self.test_user, self.strava_client, self.date_start, self.date_end, limit=2)
    # Check that there are the correct number of activities
    self.assertEqual(len(test_activities), 2)
    # Check that returned objects are of the correct type
    self.assertIsInstance(test_activities[0], Activity) 

  # Test that points can be sampled
  #@skip("Writing tests...")
  def test_extract_points(self):
    test_activity = get_strava_activities(self.test_user, self.strava_client, self.date_start, self.date_end, limit=2)[0]
    test_stream = self.strava_client.get_activity_streams(activity_id = test_activity, types = ["latlng"], resolution ='medium')
    extracted_points = extract_points(test_stream)
    extracted_multipoint = extracted_points.get("points")
    extracted_json = extracted_points.get("json")
    # Check that returned objects are of the correct types
    self.assertIsInstance(extracted_multipoint, MultiPoint)
    self.assertEqual(extracted_json.get("type"), "MultiPoint")
    # Reverse coordinate order so we can compare with original points
    sampled_points = extracted_json.get("coordinates")
    sampled_reversed = list(map(lambda coords: coords[::-1], sampled_points))
    original_points = test_stream.get("latlng").data
    # Check that the sampled points are contained within the original points
    self.assertTrue(all(map(original_points.__contains__, sampled_reversed)))

class GetEarthDataTests(TestCase):
  """
  Test that google earth engine data can be fetched
  """

  def setUp(self):
    self.sampling_points = {
      "type": "MultiPoint",
      "coordinates": 
      [
          [-110.71, 32.31],
          [-110.68, 32.32],
          [-110.66, 32.30]
      ]
    }
    self.earth_data = {
      'data_list': 
      [
        1259.68603515625, 
        1422.365966796875,
        945.7147216796875
      ]
    }
  
  # Test that querying earth engine data and sampling the data at test points returns the correct data
  #@skip("Writing tests...")
  def test_get_earth_data(self):
    test_earth_data = get_earth_data("USGS/3DEP/1m", self.sampling_points, get_url=False)
    self.assertEqual(test_earth_data, self.earth_data)
      
  # Test that returned url contains the right scheme, subdomain, second-level domain, and top-level domain
  #@skip("Writing tests...")
  def test_get_earth_data_url(self):
    test_earth_data = get_earth_data("USGS/3DEP/1m", self.sampling_points, get_url=True)
    self.assertRegex(test_earth_data.get("data_url"), "https:\/\/earthengine\.googleapis\.com")