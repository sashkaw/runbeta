# Generated by Django 4.1.1 on 2022-10-12 20:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("register", "0002_alter_user_options_alter_user_managers_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="stravaDetails",
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
                ("strava_access_token", models.CharField(max_length=300)),
                ("hr_target_low", models.IntegerField()),
                ("hr_target_med", models.IntegerField()),
                ("hr_target_high", models.IntegerField()),
                (
                    "user_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="route",
            name="user_id",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.DeleteModel(
            name="User",
        ),
    ]
