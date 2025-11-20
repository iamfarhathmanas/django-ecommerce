import random
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import OneTimePassword, User


def generate_otp(user: User, purpose: str) -> OneTimePassword:
    code = f"{random.randint(100000, 999999)}"
    expiry = timezone.now() + timedelta(minutes=10)
    otp = OneTimePassword.objects.create(
        user=user,
        code=code,
        purpose=purpose,
        expires_at=expiry,
    )
    subject = f"{settings.APP_NAME if hasattr(settings, 'APP_NAME') else 'Manas Shop'} OTP"
    send_mail(subject, f"Your OTP is {code}", None, [user.email], fail_silently=True)
    return otp


def verify_otp(user: User, code: str, purpose: str) -> bool:
    otp = (
        OneTimePassword.objects.filter(user=user, code=code, purpose=purpose)
        .order_by("-created_at")
        .first()
    )
    if not otp or not otp.is_valid:
        return False
    otp.mark_used()
    if purpose == OneTimePassword.Purpose.VERIFY:
        user.is_phone_verified = True
        user.save(update_fields=["is_phone_verified"])
    return True

