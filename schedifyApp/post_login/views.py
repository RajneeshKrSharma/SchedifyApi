from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PostLoginAppData, Address, PostLoginUserDetail
from .serializers import PostLoginAppDataSerializer, PostLoginUserDetailSerializer
from ..CustomAuthentication import CustomAuthentication
from ..address.serializers import AddressSerializer
from ..login.models import AppUser


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


class PostLoginUserDetailView(APIView):
    """
    Handles GET (retrieve), POST (create), PUT/PATCH (update), DELETE (remove)
    for the logged-in user only.
    """

    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        linked_user_id = request.app_user.id
        detail = get_object_or_404(PostLoginUserDetail, user_id=linked_user_id)
        serializer = PostLoginUserDetailSerializer(detail)
        return Response(serializer.data)

    def post(self, request):
        linked_user_id = request.app_user.id
        request.data["user"] = linked_user_id  # force user to be current user
        serializer = PostLoginUserDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        linked_user_id = request.app_user.id
        detail = get_object_or_404(PostLoginUserDetail, user_id=linked_user_id)
        request.data["user"] = linked_user_id  # enforce linked user
        serializer = PostLoginUserDetailSerializer(detail, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        linked_user_id = request.app_user.id
        detail = get_object_or_404(PostLoginUserDetail, user_id=linked_user_id)
        request.data["user"] = linked_user_id
        serializer = PostLoginUserDetailSerializer(detail, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        linked_user_id = request.app_user.id
        detail = get_object_or_404(PostLoginUserDetail, user_id=linked_user_id)
        detail.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)