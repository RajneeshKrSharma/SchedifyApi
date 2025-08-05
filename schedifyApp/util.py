from datetime import datetime

from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

# Function to create JWT token
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)  # This line should be updated
    access = AccessToken.for_user(user)  # Create the access token similarly
    return {
        'refresh': str(refresh),
        'access': str(access),
    }


from rest_framework import serializers
from datetime import datetime
from django.utils import timezone
import pytz


class CustomDateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        if value is None:
            return None

        ist = pytz.timezone("Asia/Kolkata")
        value = timezone.localtime(value, ist)
        return value.strftime('%Y-%m-%d %H:%M')

    def to_internal_value(self, data):
        # Accept nulls only if allowed
        if data in [None, '', 'null']:
            if self.allow_null:
                return None
            raise serializers.ValidationError("This field may not be null.")

        try:
            parsed_datetime = datetime.strptime(data, '%Y-%m-%d %H:%M')
            ist = pytz.timezone("Asia/Kolkata")
            aware_datetime = ist.localize(parsed_datetime)

            if aware_datetime <= timezone.now().astimezone(ist):
                raise serializers.ValidationError("Datetime cannot be in the past.")

            return aware_datetime
        except ValueError:
            raise serializers.ValidationError("Invalid datetime format. Use 'YYYY-MM-DD HH:MM'.")


class CustomDateTimeFieldWithoutValidation(serializers.DateTimeField):
    def to_representation(self, value):
        if value is None:
            return None

        ist = pytz.timezone("Asia/Kolkata")
        value = timezone.localtime(value, ist)
        return value.strftime('%Y-%m-%d %H:%M')

    def to_internal_value(self, data):
        # Accept nulls only if allowed
        if data in [None, '', 'null']:
            if self.allow_null:
                return None
            raise serializers.ValidationError("This field may not be null.")

        try:
            parsed_datetime = datetime.strptime(data, '%Y-%m-%d %H:%M')
            ist = pytz.timezone("Asia/Kolkata")
            aware_datetime = ist.localize(parsed_datetime)

            return aware_datetime
        except ValueError:
            raise serializers.ValidationError("Invalid datetime format. Use 'YYYY-MM-DD HH:MM'.")