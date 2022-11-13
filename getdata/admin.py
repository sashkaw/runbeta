from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from .models import Activity

# Register your models here.
@admin.register(Activity)
class ActivityAdmin(OSMGeoAdmin):
  # Select which fields to display in admin view
  list_display = (
    "user_id", 
    "activity_id", 
    "start_date", 
    "created_date", 
    "time",
    "latlng",
    "distance",
    "velocity_smooth",
    "heartrate",
    "elevation")