from django.urls import path, include
from rest_framework.routers import DefaultRouter

from schedifyApp.before_login.views import AppDetailsAPIView

# Define the urlpatterns for this package
urlpatterns = [
    path('info', AppDetailsAPIView.as_view(), name='appdetails'),
]