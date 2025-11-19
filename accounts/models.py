from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        validators=[RegexValidator(r"^[0-9+()-]+$", "Enter a valid phone number.")],
    )
    is_phone_verified = models.BooleanField(default=False)
    marketing_opt_in = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to="users/avatars/", blank=True, null=True)
    default_currency = models.CharField(max_length=5, default="INR")
    date_of_birth = models.DateField(null=True, blank=True)
    last_otp_sent_at = models.DateTimeField(null=True, blank=True)

    REQUIRED_FIELDS = ["email"]

    def save(self, *args, **kwargs):
        if not self.username:
            # allow username-less signup by falling back to email or phone
            fallback = self.email or self.phone_number
            if fallback:
                self.username = fallback.split("@")[0]
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.get_full_name() or self.email


class Address(TimeStampedModel):
    class AddressType(models.TextChoices):
        SHIPPING = "shipping", "Shipping"
        BILLING = "billing", "Billing"

    user = models.ForeignKey(
        User, related_name="addresses", on_delete=models.CASCADE
    )
    full_name = models.CharField(max_length=120)
    phone_number = models.CharField(max_length=20)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=120, default="India")
    address_type = models.CharField(
        max_length=15, choices=AddressType.choices, default=AddressType.SHIPPING
    )
    is_default = models.BooleanField(default=False)
    delivery_instructions = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ["-is_default", "city"]

    def __str__(self) -> str:
        return f"{self.full_name} - {self.city}"


class OneTimePassword(TimeStampedModel):
    class Purpose(models.TextChoices):
        LOGIN = "login", "Login"
        RESET = "reset", "Password Reset"
        VERIFY = "verify", "Verification"

    user = models.ForeignKey(
        User, related_name="otps", on_delete=models.CASCADE
    )
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def mark_used(self):
        self.is_used = True
        self.save(update_fields=["is_used"])

    @property
    def is_valid(self) -> bool:
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self) -> str:
        return f"{self.user.email} - {self.purpose}"
