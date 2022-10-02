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

from .models import User, Route


# Function to display test message on home page (index.html)
class IndexView(generic.ListView):
  template_name = "authstrava/index.html"
  context_object_name = "latest_user_list"

  def get_queryset(self):
    # Return last 5 created users (not including ones published in the future)
    return User.objects.filter(
      creation_date__lte=timezone.now()
      ).order_by("-creation_date")[:5]
