from rest_framework import serializers

from schedifyApp.schedule_list.models import ScheduleItemList, ScheduleListAttachments, ScheduleNotificationStatus
from schedifyApp.util import CustomDateTimeField

class ScheduleListAttachmentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleListAttachments
        fields = ['file']

    def to_representation(self, instance):
        return instance.file.url


class ScheduleItemListSerializers(serializers.ModelSerializer):
    dateTime = CustomDateTimeField()
    attachments = ScheduleListAttachmentUploadSerializer(many=True, read_only=True)

    class Meta:
        model = ScheduleItemList
        fields = ['id', 'dateTime', 'title', 'lastScheduleOn', 'isWeatherNotifyEnabled',
                  'isItemPinned', 'subTitle', 'isArchived',
                  'priority', 'user_id', "attachments"]


class ScheduleNotificationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleNotificationStatus
        fields = '__all__'