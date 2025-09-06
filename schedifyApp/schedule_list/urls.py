from django.urls import path

from schedifyApp.schedule_list.views import ScheduleItemView, ScheduleNotificationStatusAPIView

urlpatterns = [
    path('schedule-items', ScheduleItemView.as_view()),
    path('schedule-items/<int:item_id>', ScheduleItemView.as_view()),
    path('schedule-notification-status', ScheduleNotificationStatusAPIView.as_view(), name='schedule-status-list'),
]