from django.urls import path

from schedifyApp.schedule_list.views import ScheduleItemView, UploadScheduleAttachmentsView, \
    ScheduleNotificationStatusAPIView

urlpatterns = [
    path('schedule-items', ScheduleItemView.as_view()),
    path('schedule-items/<int:item_id>', ScheduleItemView.as_view()),
    path('schedule-items/upload-attachments', UploadScheduleAttachmentsView.as_view(), name='upload-attachments'),
    path('schedule-notification-status', ScheduleNotificationStatusAPIView.as_view(), name='schedule-status-list'),
]