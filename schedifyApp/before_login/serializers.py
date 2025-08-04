from rest_framework import serializers
from .models import AppDetails, AppSpecificDetails, AppUpdateInfo, AppTourInfo


# Serializer for AppSpecificDetails
class AppSpecificDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppSpecificDetails
        fields = ['language_code', 'theme']  # Make sure field names match model

# Serializer for AppUpdateInfo
class AppUpdateInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUpdateInfo
        fields = ['redirect_url', 'current_version', 'update_mode']  # Make sure field names match model

# Serializer for AppTourInfo
class AppTourInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppTourInfo
        fields = ['title', 'subtitle', 'image']  # Make sure field names match model


# Serializer for AppDetails with nested serializers
class AppDetailsSerializer(serializers.ModelSerializer):
    app_specific_details = AppSpecificDetailsSerializer()
    app_update_info = AppUpdateInfoSerializer()
    app_tour_info = AppTourInfoSerializer(many=True)

    class Meta:
        model = AppDetails
        fields = ['app_specific_details', 'app_update_info', 'app_tour_info']  # Ensure fields match model
