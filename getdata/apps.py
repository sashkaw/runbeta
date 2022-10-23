# Django imports
from django.apps import AppConfig

# Package imports
import os
from dotenv import load_dotenv
import json
import ee

class GetdataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "getdata"

    # Use AppConfig.ready() to run Google Earth Engine authentication code once when application starts up
    def ready(self):
        # Get path to secrets file
        load_dotenv()

        # Get name of account
        EARTH_ENGINE_ACCOUNT = os.getenv("EARTH_ENGINE_ACCOUNT")

        # Authenticate
        credentials = ee.ServiceAccountCredentials(EARTH_ENGINE_ACCOUNT, "./earth_engine_account.json")
        ee.Initialize(credentials)


