from rest_framework import serializers
from .models import AppDetails, AppSpecificDetails, AppUpdateInfo, AppTourInfo, HomeCarouselBanner, HomeCellDetails


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

class HomeCarouselBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeCarouselBanner
        fields = ['id', 'title', 'subtitle', 'image_url', 'background_gradient_colors']


class HomeCellDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeCellDetails
        fields = ['id', 'title', 'image_url', 'description', 'background_gradient_colors', 'title_color']

# Serializer for AppDetails with nested serializers
class AppDetailsSerializer(serializers.ModelSerializer):
    app_specific_details = AppSpecificDetailsSerializer()
    app_update_info = AppUpdateInfoSerializer()
    app_tour_info = AppTourInfoSerializer(many=True)
    home_carousel_banners = HomeCarouselBannerSerializer(many=True)
    home_cell_details = HomeCellDetailsSerializer(many=True)

    class Meta:
        model = AppDetails
        fields = ['app_specific_details', 'app_update_info', 'app_tour_info', 'home_carousel_banners', 'home_cell_details']  # Ensure fields match model
