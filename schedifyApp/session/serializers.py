from rest_framework import serializers
from .models import SessionDataConfig, Session
from ..util import CustomDateTimeField


class SessionDataConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionDataConfig
        fields = '__all__'


class SessionSerializer(serializers.ModelSerializer):
    preAuthSessionCreatedAt = CustomDateTimeField(allow_null=True, required=False)
    postAuthSessionCreatedAt = CustomDateTimeField(allow_null=True, required=False)
    postAuthSessionRefreshedAt = CustomDateTimeField(allow_null=True, required=False)
    preAuthSessionRefreshedAt = CustomDateTimeField(allow_null=True, required=False)

    class Meta:
        model = Session
        fields = ["id", "preAuthSessionCreatedAt", "postAuthSessionCreatedAt",
                  "preAuthSessionRefreshedAt", "postAuthSessionRefreshedAt",
                  "isPreAuthDataRefreshValue", "isPostAuthDataRefreshValue", "user"]

    def validate_user(self, value):
        # Only enforce uniqueness if creating a new session
        if self.instance is None and Session.objects.filter(user=value).exists():
            raise serializers.ValidationError("A session already exists for this user.")
        return value
