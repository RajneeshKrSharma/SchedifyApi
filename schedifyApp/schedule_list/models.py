from datetime import datetime

import pytz
from django.contrib.auth.models import User
from django.db import models

from schedifyApp.address.models import Address, validate_pincode
from schedifyApp.login.models import EmailIdRegistration, AppUser


class ItemType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class ScheduleItemList(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, null=True)
    dateTime = models.DateTimeField()
    title = models.CharField(max_length=1000, default="Title")
    isItemPinned = models.BooleanField(default=False)
    lastScheduleOn = models.CharField(default=datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y %I:%M:%S %p'),
                                      max_length=200)
    subTitle = models.CharField(max_length=1000, default="Sub Title")
    isArchived = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    isWeatherNotifyEnabled = models.BooleanField(default=False)
    pincode = models.CharField(max_length=6, validators=[validate_pincode], null=True, blank=True)
    objects = models.Manager()


class ScheduleNotificationStatus(models.Model):
    schedule = models.OneToOneField(ScheduleItemList, on_delete=models.CASCADE, null=True)
    schedule_date_time = models.CharField(max_length=255)  # Original schedule time
    title = models.CharField(max_length=255)
    pincode = models.CharField(max_length=20)
    next_notify_at = models.CharField(
        max_length=255, null=True, blank=True
    )

    def __str__(self):
        return self.title