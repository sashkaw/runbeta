from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from .models import Route, Elevation

# Register your models here.
@admin.register(Route)
class RouteAdmin(OSMGeoAdmin):
  # Select which fields to display in admin view
  list_display = ('route_id', 'date', 'distance')