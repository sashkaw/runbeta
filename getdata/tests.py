import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Route, Elevation

# Create your tests here.


#def create_test_route(route_text):
  """
  Create a user with the given `user_text` and created the
  given number of `days` offset to now (negative for users created
  in the past, positive for user that have yet to be created).
  """
  #time = timezone.now() + datetime.timedelta(days=days)
  #return Route.objects.create_route(user_text = user_text, creation_date = time)

#class UserModelTests(TestCase):

  #def test_no_users(self):
    """
    If no users exist, display a message
    """
    #response = self.client.get(reverse("authstrava:index"))
    #self.assertEqual(response.status_code, 200)
    #self.assertContains(response, "No users are available.")
    #self.assertQuerysetEqual(response.context["latest_user_list"], [])
