from rest_framework import serializers

from schedifyApp.schedule_list.models import ScheduleItemList, ScheduleNotificationStatus
from schedifyApp.util import CustomDateTimeField


class ScheduleItemListSerializers(serializers.ModelSerializer):
    dateTime = CustomDateTimeField()
    class Meta:
        model = ScheduleItemList
        fields = ['id', 'dateTime', 'title', 'lastScheduleOn', 'isWeatherNotifyEnabled',
                  'isItemPinned', 'subTitle', 'isArchived',
                  'priority', 'user_id', 'pincode']


class ScheduleNotificationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleNotificationStatus
        fields = '__all__'