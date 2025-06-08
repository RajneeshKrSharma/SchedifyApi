from rest_framework import serializers
from .models import PostLoginAppData, BottomNavOption, WeatherNotification
from ..address.models import Address
from ..address.serializers import AddressSerializer


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


class PostLoginAppDataSerializer(serializers.ModelSerializer):
    bottom_nav_option = BottomNavOptionSerializer(many=True, read_only=True)
    weather_notification = WeatherNotificationSerializer(many=True, read_only=True)

    class Meta:
        model = PostLoginAppData
        fields = ['id', 'bottom_nav_option', 'weather_notification']
