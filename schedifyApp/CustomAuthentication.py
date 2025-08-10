from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from schedifyApp.authenticate_user import SocialAuthentication, TokenAuthentication
from schedifyApp.login.models import AppUser


def _authenticate_with_token(request):
    """Attempts token authentication and checks for token expiry."""
    try:
        user_auth_tuple = TokenAuthentication().authenticate(request)
        if user_auth_tuple is None:
            raise AuthenticationFailed('Invalid token')

        user, auth_token = user_auth_tuple  # Extract user and token

        # Check if the token has expired
        if auth_token.expires_at < timezone.now():
            raise AuthenticationFailed('Token has expired')

        return user, auth_token  # Return authenticated user and valid token

    except AuthenticationFailed as e:
        raise AuthenticationFailed(f'Token authentication failed: {str(e)}')


def _authenticate_with_social_or_token(request):
    """Attempts social authentication first, then falls back to token authentication."""
    try:
        return SocialAuthentication().authenticate(request)  # Try social authentication
    except AuthenticationFailed as e:
        # If social authentication fails, attempt regular token authentication
        return _authenticate_with_token(request)


def _get_app_user(user, auth_header):
    from schedifyApp.login.models import EmailIdRegistration
    from django.db import transaction

    if "Bearer" in auth_header:
        # Social user login: 'user' is expected to be social_user instance
        app_user, created = AppUser.objects.get_or_create(
            social_user=user,
            app_user_email=user.email,
            defaults={}
        )
        return app_user
    else:
        # Email OTP user login: 'user' is expected to be a CustomUser or username string
        # So first get EmailIdRegistration instance
        if isinstance(user, EmailIdRegistration):
            email_otp_user = user
        else:
            # If user is CustomUser or string username, fetch EmailIdRegistration
            # Adjust attribute name according to your CustomUser model
            try:
                email_otp_user = EmailIdRegistration.objects.get(emailId=user.emailIdLinked.emailId)
            except Exception:
                # fallback if emailIdLinked missing
                raise ValueError("Unable to find EmailIdRegistration for given user")

        app_user, created = AppUser.objects.get_or_create(
            email_otp_user=email_otp_user,
            app_user_email= email_otp_user.emailId,
            defaults={}
        )
        return app_user

class CustomAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Get the Authorization header
        auth_header = request.headers.get('Authorization')

        # Check if the Authorization header is present
        if not auth_header:
            raise AuthenticationFailed('Authorization header missing')

        # Case 1: Bearer token-based authentication
        if auth_header.startswith('Bearer '):
            user, auth_token = _authenticate_with_social_or_token(request)
        else:
            # Case 2: Token-based without Bearer (for regular TokenAuthentication check)
            user, auth_token = _authenticate_with_token(request)

        print("user: ", user)
        # Centralized AppUser fetch
        app_user = _get_app_user(user, auth_header)
        request.app_user = app_user  # Attach directly to request
        return user, auth_token

    def authenticate_header(self, request):
        """
        Returns the `WWW-Authenticate` header for unauthenticated requests.
        """
        return 'Bearer'

