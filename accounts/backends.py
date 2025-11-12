from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend:
    """Custom authentication backend using email instead of username"""

    def authenticate(self, request, username=None, password=None):
        """Authenticate using email and password"""
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        """Get user by ID"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def user_can_authenticate(user):
        """Check if user is active"""
        return getattr(user, 'is_active', True)
