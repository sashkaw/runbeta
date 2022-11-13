"""from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client
import unittest


# Test to create a user and test that user login is successful
class LoginTestCase(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('sergio', 'mendes@brasil.com', 'musicislife')

    def testLogin(self):
        self.client.login(username='sergio', password='musicislife')
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)"""