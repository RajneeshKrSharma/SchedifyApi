from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AppDetails
from .serializers import AppDetailsSerializer

class AppDetailsAPIView(APIView):
    """
    Handles creation, retrieval, update, and delete of AppDetails.
    If multiple records exist, only the first one will be returned.
    """

    def get(self, request):
        queryset = AppDetails.objects.all()
        if not queryset.exists():
            return Response({"detail": []}, status=status.HTTP_200_OK)

        instance = queryset.first()
        serializer = AppDetailsSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AppDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        queryset = AppDetails.objects.all()
        if not queryset.exists():
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        instance = queryset.first()
        serializer = AppDetailsSerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        queryset = AppDetails.objects.all()
        if not queryset.exists():
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        instance = queryset.first()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
