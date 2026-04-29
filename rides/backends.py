from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class PhoneNumberBackend(ModelBackend):
    """Authenticate with phone number stored in Profile."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        phone_number = username or kwargs.get('phone_number')
        if phone_number is None or password is None:
            return None

        # First try to authenticate by phone number in Profile
        try:
            profile = User.objects.get(profile__phone_number=phone_number).profile
            user = profile.user
        except User.DoesNotExist:
            # fallback to default username
            try:
                user = User.objects.get(username=phone_number)
            except User.DoesNotExist:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
