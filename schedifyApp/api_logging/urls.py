from django.urls import path
from .views import api_logs_page, api_logs_json, clear_logs

urlpatterns = [
    path("logs", api_logs_page, name="api_logs_page"),
    path("logs/data/", api_logs_json, name="api_logs_json"),
    path("logs/data/clear", clear_logs, name="clear_logs"),
]