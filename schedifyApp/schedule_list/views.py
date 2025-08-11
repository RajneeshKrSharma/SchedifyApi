from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from schedifyApp.CustomAuthentication import CustomAuthentication
from schedifyApp.schedule_list.models import ScheduleItemList, ScheduleListAttachments, ScheduleNotificationStatus
from schedifyApp.schedule_list.serializers import ScheduleItemListSerializers, \
    ScheduleListAttachmentUploadSerializer, ScheduleNotificationStatusSerializer

from rest_framework.views import APIView

# class CustomBaseAuthenticatedView(APIView):
#     """
#     Base view to handle token differentiation and user type logic.
#     """
#     authentication_classes = [CustomAuthentication]
#     permission_classes = [IsAuthenticated]
#
#     def get_user_data(self, request):
#         """
#         Return the appropriate user type and related user identifier.
#         """
#         user = request.user
#
#
#         if hasattr(user, "google_auth_user_id"):  # Social user
#             return user, {"google_auth_user_id": user.id}
#         elif hasattr(user, "emailIdLinked_id"):  # Custom user
#             return user, {"user_id": user.emailIdLinked_id}
#         else:
#             raise ValueError("Unknown user type")
#
#     def filter_queryset(self, queryset, user_filter):
#         """
#         Filter the queryset based on user-specific filters.
#         """
#         return queryset.filter(**user_filter)
#
#
# class ScheduleItemView(CustomBaseAuthenticatedView):
#     def get(self, request, item_id=None):
#         user, user_filter = self.get_user_data(request)
#         if item_id:
#             user_filter["id"] = item_id
#         schedule_items = self.filter_queryset(ScheduleItemList.objects, user_filter)
#
#         if not schedule_items.exists():
#             return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         serializer = ScheduleItemListSerializers(schedule_items, many=True)
#         return Response({"data": serializer.data}, status=status.HTTP_200_OK)

class ScheduleItemView(APIView):
    authentication_classes = [CustomAuthentication]  # Use the custom authentication class
    permission_classes = [IsAuthenticated]

    # @staticmethod
    # def authenticate_user(request):
    #     """Authenticate user based on the token provided in the headers."""
    #     token = request.META.get('HTTP_AUTHORIZATION', b'')
    #     try:
    #         token_instance = AuthToken.objects.get(key=token)
    #         return token_instance.user
    #     except AuthToken.DoesNotExist:
    #         return None

    def get(self, request, item_id=None):
        """Handle GET requests to retrieve schedule items."""
        user = request.app_user

        if not user:
            return Response({"error": "Invalid user"}, status=status.HTTP_401_UNAUTHORIZED)

        if item_id:
            user_scheduled_object = ScheduleItemList.objects.get(user_id=user.id, id=item_id)

            if not user_scheduled_object:
                return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = ScheduleItemListSerializers(user_scheduled_object)
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            schedule_list_items = ScheduleItemList.objects.filter(user_id=user.id)

            serializer = ScheduleItemListSerializers(schedule_list_items, many=True)


        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        """Handle POST requests to create a schedule item."""
        user = request.app_user

        if not user:
            return Response({"error": "Invalid user"}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = ScheduleItemListSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save(user_id=user.id)

            return Response(
                {'message': "Your Scheduled Data Saved Successfully", 'data': serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, item_id=None):
        """Handle PATCH requests to update a schedule item."""
        user = request.app_user

        if not user:
            return Response({"error": "Invalid user"}, status=status.HTTP_401_UNAUTHORIZED)

        if not item_id:
            return Response({"error": "Provide item id"}, status=status.HTTP_400_BAD_REQUEST)

        schedule_item = get_object_or_404(ScheduleItemList, id=item_id, user_id=user.id)
        serializer = ScheduleItemListSerializers(schedule_item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data}, status=status.HTTP_200_OK)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, item_id = None):
        """Handle DELETE requests to delete a schedule item."""
        user = request.app_user

        if not user:
            return Response({"error": "Invalid user"}, status=status.HTTP_401_UNAUTHORIZED)

        if not item_id:
            return Response({"error": "Provide item id"}, status=status.HTTP_400_BAD_REQUEST)

        schedule_item = get_object_or_404(ScheduleItemList, id=item_id, user_id=user.id)
        schedule_item.delete()
        remaining_items = ScheduleItemList.objects.filter(user_id=user.id)
        serializer = ScheduleItemListSerializers(remaining_items, many=True)
        return Response(
            {
                'message': "Scheduled item deleted successfully.",
                "remainingItems": serializer.data,
            },
            status=status.HTTP_200_OK
        )


class UploadScheduleAttachmentsView(APIView):
    authentication_classes = [CustomAuthentication]  # Use the custom authentication class
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        schedule_id = request.data.get('schedule_id')
        try:
            schedule = ScheduleItemList.objects.get(id=schedule_id)
        except ScheduleItemList.DoesNotExist:
            return Response({"error": "Schedule not found."}, status=status.HTTP_404_NOT_FOUND)

        files = request.FILES.getlist('files')
        uploaded_files = []

        for f in files:
            attachment = ScheduleListAttachments.objects.create(
                user=schedule,
                file=f
            )
            uploaded_files.append(attachment)

        serializer = ScheduleListAttachmentUploadSerializer(uploaded_files, many=True)
        return Response({"attachments": serializer.data}, status=status.HTTP_201_CREATED)


class ScheduleNotificationStatusAPIView(APIView):
    authentication_classes = [CustomAuthentication]  # Use the custom authentication class
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all schedule notification statuses"""
        statuses = ScheduleNotificationStatus.objects.all()
        serializer = ScheduleNotificationStatusSerializer(statuses, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new schedule notification status"""
        serializer = ScheduleNotificationStatusSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """Partially update an existing schedule notification status"""
        id = request.query_params.get('id')

        try:
            status_obj = ScheduleNotificationStatus.objects.get(pk=id)
        except ScheduleNotificationStatus.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ScheduleNotificationStatusSerializer(status_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request):
        """Delete a schedule notification status"""
        id = request.query_params.get('id')

        try:
            status_obj = ScheduleNotificationStatus.objects.get(pk=id)
        except ScheduleNotificationStatus.DoesNotExist:
            return Response({"data": "No data exists"}, status=status.HTTP_200_OK)

        status_obj.delete()
        return Response({"data": "No data exists"}, status=status.HTTP_200_OK)
