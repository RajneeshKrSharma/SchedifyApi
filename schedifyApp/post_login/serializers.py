from rest_framework import serializers
from .models import PostLoginAppData, BottomNavOption, WeatherNotification, HomeCellAction, HomeCellDetails, \
    HomeCarouselBanner, PostLoginUserDetail


# Serializer for BottomNavOption
class BottomNavOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BottomNavOption
        fields = ['id', 'title', 'subtitle', 'is_default_selected', 'icon_url', 'is_allowed', 'is_disabled']


# Serializer for WeatherNotification
class WeatherNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherNotification
        fields = ['id', 'info']

class HomeCarouselBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeCarouselBanner
        fields = ['id', 'title', 'subtitle', 'image_url', 'background_gradient_colors']

class HomeCellActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeCellAction
        fields = ['action_screen_name', 'metadata']


class HomeCellDetailsSerializer(serializers.ModelSerializer):
    action = HomeCellActionSerializer()

    class Meta:
        model = HomeCellDetails
        fields = ['id', 'title', 'image_url', 'description', 'background_gradient_colors', 'title_color', 'action']


class PostLoginAppDataSerializer(serializers.ModelSerializer):
    bottom_nav_option = BottomNavOptionSerializer(many=True, read_only=True)
    weather_notification = WeatherNotificationSerializer(many=True, read_only=True)
    home_carousel_banners = HomeCarouselBannerSerializer(many=True)
    home_cell_details = HomeCellDetailsSerializer(many=True)

    class Meta:
        model = PostLoginAppData
        fields = ['id', 'bottom_nav_option', 'weather_notification', 'home_carousel_banners', 'home_cell_details']


class PostLoginUserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLoginUserDetail
        fields = ["id", "fcmToken", "user"]
