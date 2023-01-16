from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.gis.geos import Point, LineString, MultiLineString
from uploadgpx.forms import UploadGpxForm
from uploadgpx.models import GpxFile, GpxPoint, GpxTrack
from django.conf import settings

import gpxpy
import gpxpy.gpx #what is this, is it necessary?

# function for parsing and saving data from gpx file to database
# function is called after the gpx_file is uploaded

def SaveGPXtoPostGIS(f, file_instance):
    gpx_file = open(settings.MEDIA_ROOT+ '/uploaded_gpx_files'+'/' + f.name)
    gpx = gpxpy.parse(gpx_file)

    if gpx.waypoints:
        for waypoint in gpx.waypoints:
            new_waypoint = GpxPoint()
            if waypoint.name:
                new_waypoint.name = waypoint.name
            else:
                new_waypoint.name = 'unknown'
            new_waypoint.point = Point(waypoint.longitude, waypoint.latitude)
            new_waypoint.gpx_file = file_instance
            new_waypoint.save()

    if gpx.tracks:
        for track in gpx.tracks:
            print ("track name:" + str(track.name))
            new_track = GpxTrack()
            for segment in track.segments:
                track_list_of_points = []
                for point in segment.points:
                    point_in_segment = Point(point.longitude, point.latitude)
                    track_list_of_points.append(point_in_segment.coords)
                new_track_segment = LineString(track_list_of_points)
            new_track.track = MultiLineString(new_track_segment)
            new_track.gpx_file = file_instance
            new_track.save()

def upload_gpx(request):
    template = 'uploadgpx/uploadgpx.html'
    if request.method =='POST':
        file_instance = GpxFile()
        form = UploadGpxForm(request.POST, request.FILES, instance=file_instance)
        if form.is_valid():
            form.save()
            SaveGPXtoPostGIS(request.FILES['gpx_file'], file_instance)
            return HttpResponseRedirect('success/') #or some indication of success
    else:
        form = UploadGpxForm()

    return render(request, template, {'form':form})

def upload_success(request):
    return render('uploadgpx/success.html')