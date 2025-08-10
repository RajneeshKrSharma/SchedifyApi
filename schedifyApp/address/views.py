# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Address
from .serializers import AddressSerializer
from ..CustomAuthentication import CustomAuthentication


class AddressView(APIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        address = Address.objects.filter(user_id=request.app_user.id).first()
        if address:
            return Response(AddressSerializer(address).data)
        return Response({"detail": "No address found."}, status=404)

    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            # Optional: force the user field to match the logged-in user
            serializer.save(user_id=request.app_user.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
