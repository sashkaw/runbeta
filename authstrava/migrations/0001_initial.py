# Generated by Django 4.1.1 on 2022-10-02 07:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("user_name", models.CharField(max_length=200)),
                ("creation_date", models.DateField(verbose_name="date created")),
                (
                    "strava_email",
                    models.CharField(default="test_email", max_length=200),
                ),
                (
                    "strava_client_id",
                    models.CharField(default="test_client_id", max_length=200),
                ),
                (
                    "strava_client_secret",
                    models.CharField(default="test_client_secret", max_length=200),
                ),
                (
                    "strava_access_token",
                    models.CharField(default="test_access", max_length=200),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Route",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("route_name", models.CharField(max_length=200)),
                ("date", models.DateTimeField(verbose_name="date completed")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="authstrava.user",
                    ),
                ),
            ],
        ),
    ]
