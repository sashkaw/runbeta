# Generated by Django 4.1.1 on 2023-02-02 23:19

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion
import uploadgpx.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GpxFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='Title')),
                ('gpx_file', models.FileField(blank=True, upload_to=uploadgpx.models.GpxFolder)),
            ],
        ),
        migrations.CreateModel(
            name='GpxTrack',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('track', django.contrib.gis.db.models.fields.MultiLineStringField(srid=4326)),
                ('gpx_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='uploadgpx.gpxfile')),
            ],
        ),
        migrations.CreateModel(
            name='GpxPoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=50, verbose_name='Name')),
                ('description', models.CharField(blank=True, max_length=250, verbose_name='Description')),
                ('point', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('gpx_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='uploadgpx.gpxfile')),
            ],
        ),
    ]
