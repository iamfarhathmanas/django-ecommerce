from django.contrib.auth import authenticate, get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Address, OneTimePassword
from .serializers import AddressSerializer, OTPSerializer, RegisterSerializer, UserSerializer
from .services import generate_otp, verify_otp

User = get_user_model()


class AuthViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in {"register", "login", "request_otp", "verify_otp"}:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "register":
            return RegisterSerializer
        if self.action in {"create_address", "addresses"}:
            return AddressSerializer
        if self.action in {"request_otp", "verify_otp"}:
            return OTPSerializer
        return UserSerializer

    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request):
        identifier = request.data.get("identifier")
        password = request.data.get("password")
        user = authenticate(request, username=identifier, password=password)
        if not user:
            return Response({"detail": "Invalid credentials."}, status=400)
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        )

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=["get"], url_path="addresses")
    def addresses(self, request):
        serializer = AddressSerializer(request.user.addresses.all(), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="addresses")
    def create_address(self, request):
        serializer = AddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="request-otp")
    def request_otp(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data["identifier"]
        purpose = serializer.validated_data["purpose"]
        try:
            user = User.objects.get(email=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(phone_number=identifier)
            except User.DoesNotExist:
                return Response({"detail": "User not found."}, status=404)
        otp = generate_otp(user, purpose)
        return Response({"expires_at": otp.expires_at}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="verify-otp")
    def verify_otp(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data["identifier"]
        code = serializer.validated_data["code"]
        purpose = serializer.validated_data["purpose"]
        user = User.objects.filter(email=identifier).first() or User.objects.filter(
            phone_number=identifier
        ).first()
        if not user:
            return Response({"detail": "User not found."}, status=404)
        if not verify_otp(user, code, purpose):
            return Response({"detail": "Invalid OTP"}, status=400)
        payload = {"verified": True}
        if purpose == OneTimePassword.Purpose.LOGIN:
            refresh = RefreshToken.for_user(user)
            payload["refresh"] = str(refresh)
            payload["access"] = str(refresh.access_token)
        return Response(payload)

