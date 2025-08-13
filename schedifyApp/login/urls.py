from django.urls import path

from schedifyApp.login import views
from schedifyApp.login.views import CheckDuplicateEmailView

urlpatterns = [
    path("get-otp", views.get_otp_api, name="get-otp"),
    path("login-via-otp", views.login_via_otp, name="login-via-otp"),
    path('check-duplicate-email', CheckDuplicateEmailView.as_view(), name='check-duplicate-email'),
]
