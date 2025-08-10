from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import PostLoginAppData, Address
from .serializers import PostLoginAppDataSerializer, AddressSerializer
from ..CustomAuthentication import CustomAuthentication



class PostLoginViewSet(viewsets.ModelViewSet):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PostLoginAppDataSerializer
    http_method_names = ['get']  # or add 'post', 'put', etc., if needed

    def list(self, request, *args, **kwargs):
        user = request.app_user

        # 1. Fetch related Address
        address = Address.objects.filter(user_id=user.id).first()
        address_data = AddressSerializer(address).data if address else None

        # 2. Fetch post login data
        post_login_data = PostLoginAppData.objects.first()

        if post_login_data:
            post_data_serialized = PostLoginAppDataSerializer(post_login_data).data
            bottom_nav_data = post_data_serialized.get('bottom_nav_option', [])
            weather_notification_data = post_data_serialized.get('weather_notification', [])
            home_carousel_banners_data = post_data_serialized.get('home_carousel_banners', [])
            home_cell_details_data = post_data_serialized.get('home_cell_details', [])
        else:
            bottom_nav_data = []
            weather_notification_data = []
            home_carousel_banners_data = []
            home_cell_details_data = []

        # 3. Combine into single dict
        response_data = {
            "bottom_nav_option": bottom_nav_data,
            "weather_notification": weather_notification_data,
            "home_carousel_banners": home_carousel_banners_data,
            "home_cell_details": home_cell_details_data,
            "address_detail": address_data,
        }

        return Response(response_data, status=status.HTTP_200_OK)