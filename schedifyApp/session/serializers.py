from rest_framework import serializers
from .models import SessionDataConfig, Session


class SessionDataConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionDataConfig
        fields = '__all__'


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = '__all__'

    def validate_user(self, value):
        # Only enforce uniqueness if creating a new session
        if self.instance is None and Session.objects.filter(user=value).exists():
            raise serializers.ValidationError("A session already exists for this user.")
        return value
