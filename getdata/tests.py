# Imports
import datetime
import requests
from dotenv import load_dotenv
from unittest import mock, skip
from stravalib.client import Client

from django.test import TestCase, override_settings
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

from social_django.models import UserSocialAuth
from social_django.views import get_session_timeout

from .views import *
from .models import Activity

# Create your tests here.

# Helper function to create new users for testing
def create_user():
  new_user = User.objects.create(username='testuser', password='12345', is_active=True, is_staff=True, is_superuser=True) 
  new_user.set_password('hello') 
  new_user.save() 
  new_user = authenticate(username='testuser', password='hello') 
  #login = self.c.login(username='testuser', password='hello') 
  #self.assertTrue(login)
  return new_user

class AuthStrava(TestCase):

  # Load test fixtures
  fixtures = ["fixtures/user.json", "fixtures/socialauth.json"]

  def test_get_token(self):
    # Get user object for tests
    test_user = User.objects.get(pk=1)
    test_provider = "strava"
    # Get token
    token = get_token(user=test_user, provider=test_provider)
    self.assertIsInstance(token, str) # Check that output is a string
    self.assertGreater(len(token), 0) # Check that output has length greater than zero

  # Check that prep_strava returns a valid client object for authenticated strava user
  def test_prep_strava(self):
    # Get user object for tests
    test_user = User.objects.get(pk=1)
    #test_provider = "strava"
    test_client = prep_strava(test_user)
    #print(test_client)
    self.assertIsInstance(test_client, Client)
    #token = test_client.access_token
    #self.assertIsInstance(token, str) # Check that output is a string
    #self.assertGreater(len(token), 0) # Check that output has length greater than zero
  
  # Check that "no user" is returned when user object is not authenticated with strava
  def test_prep_strava_no_user(self):
    test_user = create_user()
    test_client = prep_strava(test_user)
    self.assertEqual(test_client, "no user")


# TODO: Add this test to check rendering strava data
"""class RenderStrava(TestCase):
  # Load test fixtures
  fixtures = ["fixtures/user.json", "fixtures/socialauth.json"]

  def test_get_token(self):
    # Get user object for tests
    test_user = User.objects.get(pk=1)
    test_provider = "strava"
    # Get token
    token = get_token(user=test_user, provider=test_provider)
    self.assertIsInstance(token, str) # Check that output is a string
    self.assertGreater(len(token), 0) # Check that output has length greater than zero"""


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
