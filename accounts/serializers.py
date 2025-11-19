from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Address

User = get_user_model()


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "updated_at")


class UserSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "phone_number",
            "is_phone_verified",
            "marketing_opt_in",
            "default_currency",
            "avatar",
            "addresses",
        )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name", "phone_number")

    def validate_password(self, value):
        validate_password(value, user=None)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data, username=validated_data["email"])
        user.set_password(password)
        user.save()
        return user


class OTPSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    code = serializers.CharField(required=False)
    purpose = serializers.CharField()

