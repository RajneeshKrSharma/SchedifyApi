from django.urls import path

from schedifyApp.session.views import SessionDataConfigAPIView, SessionAPIView

urlpatterns = [
    path('session-data-config', SessionDataConfigAPIView.as_view(), name='session-data-config'),
    path('user-sessions', SessionAPIView.as_view(), name='session-api'),
]
