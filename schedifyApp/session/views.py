from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Session, SessionDataConfig
from .serializers import SessionSerializer, SessionDataConfigSerializer
from schedifyApp.CustomAuthentication import CustomAuthentication


class SessionDataConfigAPIView(APIView):
    def get(self, _):
        try:
            config = SessionDataConfig.objects.first()
            if not config:
                return Response({"detail": "No configuration found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = SessionDataConfigSerializer(config)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SessionAPIView(APIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            session = Session.objects.get(user=request.user.id)
            serializer = SessionSerializer(session)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Session.DoesNotExist:
            return Response({"error": "No session found for this user."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id

        if Session.objects.filter(user=request.user.id).exists():
            return Response({"error": "Session for this user already exists."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SessionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        session_id = request.query_params.get('id')
        if not session_id:
            return Response({"error": "Session ID must be provided in query params."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return Response({"error": "No session found to update."}, status=status.HTTP_404_NOT_FOUND)

        serializer = SessionSerializer(session, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

