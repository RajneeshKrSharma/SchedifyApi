from rest_framework import serializers
from .models import SessionDataConfig, Session
from ..util import CustomDateTimeFieldWithoutValidation


class SessionDataConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionDataConfig
        fields = '__all__'


class SessionSerializer(serializers.ModelSerializer):
    preAuthSessionCreatedAt = CustomDateTimeFieldWithoutValidation(allow_null=True, required=False)
    postAuthSessionCreatedAt = CustomDateTimeFieldWithoutValidation(allow_null=True, required=False)
    postAuthSessionRefreshedAt = CustomDateTimeFieldWithoutValidation(allow_null=True, required=False)
    preAuthSessionRefreshedAt = CustomDateTimeFieldWithoutValidation(allow_null=True, required=False)

    class Meta:
        model = Session
        fields = ["id", "preAuthSessionCreatedAt", "postAuthSessionCreatedAt",
                  "preAuthSessionRefreshedAt", "postAuthSessionRefreshedAt",
                  "isPreAuthDataRefreshValue", "isPostAuthDataRefreshValue", "user"]
        extra_kwargs = {
            "user": {"read_only": True}
        }

    def validate_user(self, value):
        # Only enforce uniqueness if creating a new session
        if self.instance is None and Session.objects.filter(user=value).exists():
            raise serializers.ValidationError("A session already exists for this user.")
        return value
