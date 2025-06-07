from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import PostLoginAppData
from .serializers import PostLoginAppDataSerializer
from ..CustomAuthentication import CustomAuthentication


class PostLoginViewSet(viewsets.ModelViewSet):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PostLoginAppDataSerializer

    def get_queryset(self):
        user = self.request.user
        return PostLoginAppData.objects.filter(address_detail__user_id=user.emailIdLinked_id)

