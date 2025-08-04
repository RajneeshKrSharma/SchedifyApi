import jsonfield
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

class HomeCarouselBanner(models.Model):
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    image_url = models.URLField()
    background_gradient_colors = jsonfield.JSONField(blank=True, null=True)  # List of color strings

    def __str__(self):
        return self.title or "Untitled Banner"

class HomeCellAction(models.Model):
    action_description = models.CharField(
        max_length=100,
        default=""
    )

    action_type = models.IntegerField(
        default=0
    )

    metadata = jsonfield.JSONField(
        blank=True,
        null=True,
        default=dict
    )

    def __str__(self):
        return f"ActionType: {self.action_type} | {self.action_description}"

class HomeCellDetails(models.Model):
    title = models.CharField(max_length=255)
    image_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    # Store colors as hex strings (e.g., "0xFF00FF00")
    background_gradient_colors = jsonfield.JSONField(blank=True, null=True)  # List of color strings
    title_color = models.CharField(max_length=20, blank=True, null=True)
    # One-to-one mapping with HomeCellAction
    action = models.OneToOneField(HomeCellAction, on_delete=models.CASCADE, related_name="cell", null=True,  # temporarily allow null
    blank=True)

    def __str__(self):
        return self.title

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

    home_carousel_banners = models.ManyToManyField(
        HomeCarouselBanner,
        related_name="home_carousel_banners",
        blank=True,
    )
    home_cell_details = models.ManyToManyField(
        HomeCellDetails,
        related_name="home_cell_details",
        blank=True,
    )
