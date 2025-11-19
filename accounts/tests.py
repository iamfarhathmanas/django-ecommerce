"""
Tests for accounts app - authentication, profiles, addresses, OTP
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from .models import Address, OneTimePassword
from .services import generate_otp, verify_otp

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="+1234567890",
            first_name="Test",
            last_name="User",
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, "test@example.com")
        self.assertTrue(self.user.check_password("testpass123"))
        self.assertEqual(str(self.user), "test@example.com")

    def test_user_full_name(self):
        self.assertEqual(self.user.get_full_name(), "Test User")

    def test_user_str(self):
        self.assertEqual(str(self.user), "test@example.com")


class AddressModelTest(TestCase):
    """Test Address model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

    def test_address_creation(self):
        address = Address.objects.create(
            user=self.user,
            street="123 Main St",
            city="Test City",
            state="TS",
            postal_code="12345",
            country="US",
            is_default=True,
        )
        self.assertEqual(address.user, self.user)
        self.assertTrue(address.is_default)
        self.assertIn("123 Main St", str(address))


class OTPServiceTest(TestCase):
    """Test OTP generation and verification."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

    def test_generate_otp(self):
        otp = generate_otp(self.user, OneTimePassword.Purpose.LOGIN)
        self.assertIsNotNone(otp)
        self.assertEqual(otp.user, self.user)
        self.assertEqual(otp.purpose, OneTimePassword.Purpose.LOGIN)
        self.assertIsNotNone(otp.code)
        self.assertEqual(len(otp.code), 6)

    def test_verify_otp_success(self):
        otp = generate_otp(self.user, OneTimePassword.Purpose.LOGIN)
        result = verify_otp(self.user, otp.code, OneTimePassword.Purpose.LOGIN)
        self.assertTrue(result)

    def test_verify_otp_invalid_code(self):
        generate_otp(self.user, OneTimePassword.Purpose.LOGIN)
        result = verify_otp(self.user, "000000", OneTimePassword.Purpose.LOGIN)
        self.assertFalse(result)

    def test_verify_otp_expired(self):
        otp = generate_otp(self.user, OneTimePassword.Purpose.LOGIN)
        # Simulate expiration by marking as used
        otp.is_used = True
        otp.save()
        result = verify_otp(self.user, otp.code, OneTimePassword.Purpose.LOGIN)
        self.assertFalse(result)


class AuthViewsTest(TestCase):
    """Test authentication views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

    def test_login_view_get(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_login_view_post_success(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "test@example.com", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 302)  # Redirect after login

    def test_login_view_post_invalid(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "test@example.com", "password": "wrongpass"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid")

    def test_signup_view_get(self):
        response = self.client.get(reverse("accounts:signup"))
        self.assertEqual(response.status_code, 200)

    def test_signup_view_post(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "email": "newuser@example.com",
                "password1": "complexpass123",
                "password2": "complexpass123",
                "first_name": "New",
                "last_name": "User",
            },
        )
        self.assertEqual(response.status_code, 302)  # Redirect after signup
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_logout_view(self):
        self.client.login(email="test@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 302)

    def test_profile_view_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_profile_view_authenticated(self):
        self.client.login(email="test@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)


class AddressViewsTest(TestCase):
    """Test address management views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.client.login(email="test@example.com", password="testpass123")

    def test_create_address(self):
        response = self.client.post(
            reverse("accounts:add_address"),
            {
                "street": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "postal_code": "12345",
                "country": "US",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Address.objects.filter(user=self.user, street="123 Test St").exists()
        )

    def test_delete_address(self):
        address = Address.objects.create(
            user=self.user,
            street="123 Test St",
            city="Test City",
            state="TS",
            postal_code="12345",
            country="US",
        )
        response = self.client.post(reverse("accounts:delete_address", args=[address.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Address.objects.filter(id=address.id).exists())
