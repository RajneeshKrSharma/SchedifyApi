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

    def list(self, request, *args, **kwargs):
        user = request.user

        # 1. Fetch related Address
        address = Address.objects.filter(user_id=user.emailIdLinked_id).first()
        address_data = AddressSerializer(address).data if address else None

        # 2. Fetch post login data
        post_login_data = PostLoginAppData.objects.first()  # no need for `.filter().first()`

        if post_login_data:
            post_data_serialized = PostLoginAppDataSerializer(post_login_data).data
            bottom_nav_data = post_data_serialized.get('bottom_nav_option', [])
            weather_notification_data = post_data_serialized.get('weather_notification', [])
        else:
            bottom_nav_data = []
            weather_notification_data = []

        # 3. Combine into single dict
        response_data = {
            "bottom_nav_option": bottom_nav_data,
            "weather_notification": weather_notification_data,
            "address_detail": address_data
        }

        return Response(response_data, status=status.HTTP_200_OK)
