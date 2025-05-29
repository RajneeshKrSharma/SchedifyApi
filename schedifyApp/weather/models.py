from enum import Enum

from django.db import models

from schedifyApp.schedule_list.models import ScheduleItemList

class ImageAsset(models.Model):
    photo = models.ImageField(upload_to='pictures')
    date = models.DateTimeField(auto_now_add=True)

class FileAsset(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='files')


class NotifyMediumType(Enum):
    PUSH_NOTIFICATION = 'PUSH_NOTIFICATION'
    EMAIL = 'EMAIL'

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.replace('_', ' ').title()) for tag in cls]

class WeatherForecast(models.Model):
    unique_key = models.CharField(max_length=255, unique=True)  # scheduleItemId + forecast_time
    pincode = models.CharField(max_length=10)
    forecast_time = models.DateTimeField()
    timeStamp = models.BigIntegerField()
    weatherType = models.CharField(max_length=100, null=True, blank=True)
    weatherDescription = models.TextField(null=True, blank=True)
    temperature_celsius = models.FloatField(null=True, blank=True)
    humidity_percent = models.IntegerField(null=True, blank=True)
    scheduleItem = models.ForeignKey(ScheduleItemList, on_delete=models.CASCADE, related_name="schedule_list", null=True)
    updated_count = models.IntegerField()
    notify_count = models.IntegerField(null=True)
    next_notify_in = models.CharField(max_length=100, null=True, blank=True)
    next_notify_at = models.DateTimeField(null=True)
    notify_medium = models.CharField(max_length=20, choices= NotifyMediumType.choices())
    isActive = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    def __str__(self):
        return f"{self.pincode} @ {self.forecast_time}"


class WeatherPincodeMappedData(models.Model):
    pincode = models.CharField(max_length=6, unique=True)
    weather_data = models.JSONField(default={})
    last_updated = models.DateTimeField(auto_now=True)
    updated_count = models.IntegerField(default=0)

    objects = models.Manager()


class WeatherStatusImages(models.Model):
    class WeatherStatus(models.TextChoices):
        SUNNY = 'SUNNY', 'Sunny'
        CLOUDY = 'CLOUDY', 'Cloudy'
        RAINY = 'RAINY', 'Rainy'
        STORMY = 'STORMY', 'Stormy'
        SNOWY = 'SNOWY', 'Snowy'
        FOGGY = 'FOGGY', 'Foggy'
        DRIZZLY = 'DRIZZLY', 'Drizzly'
        THUNDERY = 'THUNDERY', 'Thundery'

    url = models.URLField(max_length=500)
    status = models.CharField(max_length=20, choices=WeatherStatus.choices)
    objects = models.Manager()

    def __str__(self):
        return f"{self.status} - {self.url}"
