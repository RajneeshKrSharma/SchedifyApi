"""
URL configuration for schedify project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from schedifyApp.views import encrypt_data, decrypt_data, compress_string_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('encrypt/', encrypt_data, name='encrypt-data'),
    path('decrypt/', decrypt_data, name='decrypt-data'),
    path('compress-string/', compress_string_view, name='compress-string'),
    path('auth/', include('drf_social_oauth2.urls', namespace='drf')),
    path("api/login/", include("schedifyApp.login.urls")),  # Include the login package URLs
    path("api/schedule-list/", include("schedifyApp.schedule_list.urls")),  # Include the schedule_list package URLs
    path('', include('social_django.urls', namespace='social')),
    path('api/pre/', include('schedifyApp.before_login.urls')),  # Includes all app-level URLs
    path('api/post/', include('schedifyApp.post_login.urls')),  # Includes all app-level URLs
    path('api/list/', include('schedifyApp.lists.split_expenses.urls')),  # Includes all app-level URLs
    path('api/communication/', include('schedifyApp.communication.urls')),  # Includes all app-level URLs
    path('api/address/', include('schedifyApp.address.urls')),  # Includes all app-level URLs
    path('api/weather/', include('schedifyApp.weather.urls')),  # Includes all app-level URLs
    path('helper/', include('schedifyApp.deep_links.urls')),  # Includes all app-level URLs
    path('api/session/', include('schedifyApp.session.urls')),
    path('api/bulk/', include('schedifyApp.data_insert.urls')),
    path('logging/', include('schedifyApp.api_logging.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)