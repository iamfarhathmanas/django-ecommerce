import json
from decimal import Decimal

from django.conf import settings

try:
    import stripe
except ImportError:  # pragma: no cover
    stripe = None

try:
    import razorpay
except ImportError:  # pragma: no cover
    razorpay = None


def _paise(amount: Decimal) -> int:
    return int(Decimal(amount) * 100)


def create_stripe_payment_intent(order):
    creds = settings.PAYMENT_GATEWAYS.get("stripe", {})
    if not creds.get("secret_key") or stripe is None:
        return None
    stripe.api_key = creds["secret_key"]
    intent = stripe.PaymentIntent.create(
        amount=_paise(order.total),
        currency="inr",
        metadata={"order_id": order.id},
        description=f"{settings.APP_NAME} order #{order.id}",
    )
    return intent


def verify_stripe_event(payload: bytes, signature: str):
    creds = settings.PAYMENT_GATEWAYS.get("stripe", {})
    secret = creds.get("webhook_secret")
    if not secret or stripe is None:
        return None
    try:
        return stripe.Webhook.construct_event(payload, signature, secret)
    except Exception:
        return None


def create_razorpay_order(order):
    creds = settings.PAYMENT_GATEWAYS.get("razorpay", {})
    key_id = creds.get("key_id")
    key_secret = creds.get("key_secret")
    if not key_id or not key_secret or razorpay is None:
        return None
    client = razorpay.Client(auth=(key_id, key_secret))
    data = {
        "amount": _paise(order.total),
        "currency": "INR",
        "payment_capture": 1,
        "notes": {"order_id": str(order.id)},
    }
    return client.order.create(data=data)


def verify_razorpay_signature(payload: bytes, signature: str):
    creds = settings.PAYMENT_GATEWAYS.get("razorpay", {})
    secret = creds.get("webhook_secret") or creds.get("key_secret")
    if not secret or razorpay is None or not signature:
        return None
    body = payload.decode("utf-8")
    try:
        razorpay.Utility.verify_webhook_signature(body, signature, secret)
    except razorpay.errors.SignatureVerificationError:
        return None
    return json.loads(body)

