from django.db import models

from schedifyApp.address.models import Address

class BottomNavOption(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    is_default_selected = models.BooleanField(default=False)
    icon_url = models.URLField(blank=True, null=True)
    is_allowed = models.BooleanField(default=False)
    is_disabled = models.BooleanField(default=False)

    def __str__(self):
        return self.title or "Untitled Bottom Nav Option"


class WeatherNotification(models.Model):
    info = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.info or "No Info"


class PostLoginAppData(models.Model):
    bottom_nav_option = models.ManyToManyField(
        BottomNavOption,
        related_name="post_login_app_data",
        blank=True
    )
    weather_notification = models.ManyToManyField(
        WeatherNotification,
        related_name="post_login_app_data",
        blank=True
    )
