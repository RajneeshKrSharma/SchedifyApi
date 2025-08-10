from django.urls import path

from schedifyApp.data_insert.views import HomeBulkInsertAPIView

urlpatterns = [
    path('homeDetailsBulkInsert', HomeBulkInsertAPIView.as_view(), name='group-api'),
]

