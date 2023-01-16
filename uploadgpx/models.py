from django.db import models
from django.contrib import admin
from django.contrib.gis import admin as geoadmin
from django.contrib.gis.db import models as geomodels
from django.db.models.manager import Manager
# Create your models here.

def GpxFolder(instance, filename):
    return "uploaded_gpx_files/%s" % (filename)

class GpxFile(models.Model):
    title = models.CharField("Title", max_length=100)
    gpx_file = models.FileField(upload_to=GpxFolder, blank=True)

    def __unicode__(self):
        return self.title

class GpxPoint(models.Model):
    name = models.CharField("Name", max_length = 50, blank = True)
    description = models.CharField("Description", max_length = 250, blank = True)
    gpx_file = models.ForeignKey(GpxFile, on_delete=models.CASCADE)
    point = geomodels.PointField()
    objects = models.Manager()

    def __unicode_(self):
        return (self.name)

class GpxTrack(models.Model):
    track = geomodels.MultiLineStringField() 
    gpx_file = models.ForeignKey(GpxFile, on_delete=models.CASCADE)
    objects = models.Manager()

geoadmin.site.register(GpxPoint, geoadmin.OSMGeoAdmin)
geoadmin.site.register(GpxTrack, geoadmin.OSMGeoAdmin)
admin.site.register(GpxFile)
