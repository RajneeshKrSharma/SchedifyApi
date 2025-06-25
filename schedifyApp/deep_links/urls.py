from django.urls import path

from schedifyApp.deep_links.views import deep_link_test_view

urlpatterns = [
    path("deep-link-test", deep_link_test_view, name="deep_link_test_view"),
]