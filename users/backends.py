"""
users/backends.py
==================
Custom authentication backend that authenticates using roll_number + password
instead of Django's default username/email.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class RollNumberBackend(ModelBackend):
    """
    Authenticates against roll_number field.
    Usage: authenticate(request, roll_number='SU72-BSSEM-F25-017', password='...')
    """

    def authenticate(self, request, roll_number=None, password=None, **kwargs):
        if roll_number is None or password is None:
            return None

        try:
            user = User.objects.get(roll_number=roll_number.upper().strip())
        except User.DoesNotExist:
            # Run default password hasher to prevent timing attacks
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
