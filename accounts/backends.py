from django.contrib.auth import get_user_model


class EmailOrPhoneBackend:
    """
    Allow users to log in with either email, username, or phone number.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        if not username:
            return None

        user = None
        for field in ["email", "phone_number", "username"]:
            try:
                user = User.objects.get(**{field: username})
                break
            except User.DoesNotExist:
                continue

        if user and user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

