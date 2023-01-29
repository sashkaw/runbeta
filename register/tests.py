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
from django.contrib.messages import get_messages


from social_django.models import UserSocialAuth
from social_django.views import get_session_timeout

from .views import *

# Load login info for test user
load_dotenv()
TEST_USER_NAME = os.getenv("TEST_USER_NAME")
TEST_USER_PASSWORD= os.getenv("TEST_USER_PASSWORD")
TEST_REGISTER_EMAIL=os.getenv("TEST_REGISTER_EMAIL")

# Create your tests here.

# Helper function to create new users for testing
def create_user():
  new_user = User.objects.create(username="testuser", password="12345", is_active=True, is_staff=True, is_superuser=True) 
  new_user.set_password("hello") 
  new_user.save() 
  new_user = authenticate(username="testuser", password="hello") 
  #login = self.client.login(username='testuser', password='hello') 
  #self.assertTrue(login)
  return new_user

# Test to create a user and test that user login is successful
class RegisterTestCase(TestCase):

    def setUp(self):
        self.client = djangotestcli.Client()
        #self.user = User.objects.create_user(username="sergio", email=TEST_REGISTER_EMAIL, password="musicislife", is_active=True)

    #def test_login(self):
    #    self.client.login(username="sergio", password="musicislife")
    #    response = self.client.get(reverse('index'))
    #    self.assertEqual(response.status_code, 200)
    
    def test_register(self):
        test_details = {
            "username": "sergio", 
            "email": TEST_REGISTER_EMAIL, 
            "password1": "musicislife", 
            "password2": "musicislife",
        }
        test_response = self.client.post(reverse("index"), test_details)
        self.assertRedirects(test_response, reverse("settings"))
    
    def test_register_short_pwd(self):
        test_details = {
            "username": "sergio", 
            "email": TEST_REGISTER_EMAIL, 
            "password1": "music", 
            "password2": "music",
        }
        test_response = self.client.post(reverse("index"), test_details)
        #test_messages = [m.message for m in get_messages(test_response.wsgi_request)]
        #test_messages = [m.message for m in list(test_response.context["messages"])]
        d = test_response.context["form"].errors
        print()
        #print(type(list(d.values())[0]))
        #print(vars(test_response.context["form"].errors))
        #self.assertContains(test_response.context["form"].errors, "too short", html=True)

    @skip("Writing tests...")
    def test_register_dif_pwds(self):
        test_details = {
            "username": "sergio", 
            "email": TEST_REGISTER_EMAIL, 
            "password1": "musicislife", 
            "password2": "musicisliff",
        }
        test_response = self.client.post(reverse("index"), test_details)
        print(test_response)
        #self.assertContains(test_response.context["form"].errors, "too short")
        #print(test_response.context["form"])
        #print(test_response)
        #self.assertEqual(test_response, 200)
