# Django imports
from multiprocessing import context
from re import T
from curses.ascii import HT
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
from django.contrib.auth import update_session_auth_hash, login, authenticate
from django.contrib.auth import logout as auth_logout
from django.contrib import messages

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

from .forms import RegisterForm


# Create views here:
def register(request):
  if request.method == "POST":  # check if response was submitted by the user
      form = RegisterForm(request.POST)
      if form.is_valid(): # if we got all the responses we wanted?
        user = form.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, "Registration Success!")
        #return redirect("/home")
        return redirect("/register/settings/")
        #return redirect("home/")
  else:
        form = RegisterForm()
        messages.error(request, "Registration failed")
  return render(request, "register/register.html", {"form":form}) #Add an "invalid info" message

# Built in Django user login already checks that urls are safe and looks for next parameter -> This login functon seems to be redundant
#def login(request):
#  template = "registration/login.html"
#  return render(request, template)

@login_required
def home(request):
  template = "registration/home.html"
  current_user = request.user
  context = {"user": current_user}
  return render(request, template, context)

# Built in Django user logout seems to be fine -> this function below seems to be redundant
#def logout(request):
#  url = "/login"
#  auth_logout(request)
#  return redirect(url)

# Helper function to check if access token is still valid, and if not refresh the token and return the new access token
def get_token(user, provider):
  social = user.social_auth.get(provider = provider)
  # the  ' - 10' is so that the token doesn't expire as we make the request 
  # if we check the token expiry right before it expires
  if (social.extra_data['auth_time'] + social.extra_data['expires'] - 10) <= int(time.time()):
      strategy = load_strategy() # Refresh token
      social.refresh_token(strategy)
  return social.extra_data['access_token']

# Function to show details for strava user
@login_required
def details(request):
  template = "register/details.html"
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
  return render(request, template, context)

@login_required
def settings(request):
  template = "register/settings.html"
  user = request.user

  # For testing
  current_athlete = "no athlete"
  athlete_name = "NA"

  if user.is_authenticated:
    try:
        strava_login = user.social_auth.get(provider='strava')
        strava_access_token = get_token(user, "strava") #TODO: remove one of these lines to eliminate redundancy

        # Create new client instance with the access token we generated
        client = Client(access_token = strava_access_token)

        # Get data about athlete
        current_athlete = client.get_athlete()
        athlete_name = current_athlete.firstname + " " + current_athlete.lastname
        #all_routes = client.get_routes(limit = 5)

    except UserSocialAuth.DoesNotExist:
        strava_login = None

  can_disconnect = (user.social_auth.count() >= 1 or user.has_usable_password())

  print(strava_login)

  context = {
    "strava_login": strava_login,
    "can_disconnect": can_disconnect,
    "user": user,
    "current_athlete": current_athlete,
    "athlete_name" : athlete_name,
    #"all_routes": all_routes,
}

  return render(request, template, context)

@login_required
def password(request):
  template = "register/password.html"
  
  if request.user.has_usable_password():
      PasswordForm = PasswordChangeForm
  else:
      PasswordForm = AdminPasswordChangeForm

  if request.method == 'POST':
      form = PasswordForm(request.user, request.POST)
      if form.is_valid():
          form.save()
          update_session_auth_hash(request, form.user)
          messages.success(request, 'Your password was successfully updated!')
          return redirect("/register/settings/")
      else:
          messages.error(request, 'Please correct the error below.')
  else:
      form = PasswordForm(request.user)

  context = {'form': form}
  
  return render(request, template, context)