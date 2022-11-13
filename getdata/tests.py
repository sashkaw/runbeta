import datetime
import requests
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .views import get_earth_data
from .models import Activity

# Create your tests here.

class GetEarthDataTests(TestCase):

  def test_get_earth_data_url(self):
    """
    Test that url returned from get_earth_data() returns a valid response code
    """

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
    data_url = get_earth_data(data_name="USGS/3DEP/1m", area_of_interest=test_aoi)
    print(data_url)
    # Make a request to the URL
    response = requests.get(data_url)
    self.assertEqual(response.status_code, 200)

#def create_test_route(route_text):
  #"""
  #Create a user with the given `user_text` and created the
  #given number of `days` offset to now (negative for users created
  #in the past, positive for user that have yet to be created).
  #"""
  #time = timezone.now() + datetime.timedelta(days=days)
  #return Route.objects.create_route(user_text = user_text, creation_date = time)

#class UserModelTests(TestCase):

  #def test_no_users(self):
    #"""
    #If no users exist, display a message
    #"""
    #response = self.client.get(reverse("authstrava:index"))
    #self.assertEqual(response.status_code, 200)
    #self.assertContains(response, "No users are available.")
    #self.assertQuerysetEqual(response.context["latest_user_list"], [])
