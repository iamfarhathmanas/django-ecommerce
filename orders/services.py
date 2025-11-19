from decimal import Decimal

from django.conf import settings
from django.db import transaction

from accounts.models import Address
from cart.models import Cart
from store.models import Product

from .models import Coupon, InventoryLog, Order, OrderItem, Payment
from .payment_gateways import create_razorpay_order, create_stripe_payment_intent
from .tasks import (
    send_low_stock_alert,
    send_order_created_email,
    send_order_receipt_email,
)


@transaction.atomic
def create_order_from_cart(user, address: Address, cart: Cart, coupon_code: str | None = None, delivery_fee: Decimal = Decimal("0")):
    subtotal = Decimal(cart.subtotal)
    coupon = None
    discount = Decimal("0")
    if coupon_code:
        coupon = Coupon.objects.filter(code=coupon_code, is_active=True).first()
        if coupon:
            discount = Decimal(coupon.apply(subtotal))
    total = subtotal - discount + Decimal(delivery_fee)
    order = Order.objects.create(
        user=user,
        shipping_address=address,
        coupon=coupon,
        subtotal=subtotal,
        discount=discount,
        delivery_fee=delivery_fee,
        total=total,
    )
    send_order_created_email.delay(order.id)
    for item in cart.items.select_related("product"):
        product: Product = item.product
        if product.stock < item.quantity:
            raise ValueError(f"{product.title} is out of stock.")
        product.stock -= item.quantity
        product.save(update_fields=["stock"])
        if product.stock <= settings.LOW_STOCK_THRESHOLD:
            InventoryLog.objects.create(
                product=product, change=0, reason="Low stock alert"
            )
            send_low_stock_alert.delay(product.id)
        OrderItem.objects.create(
            order=order,
            product=product,
            product_title=product.title,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        InventoryLog.objects.create(
            product=product,
            change=-item.quantity,
            reason=f"Order #{order.id}",
        )
    cart.items.all().delete()
    return order


def record_payment(
    order: Order,
    provider,
    amount: Decimal,
    status,
    transaction_id: str,
    payload: dict | None = None,
):
    provider_value = str(provider)
    status_value = str(status)
    payment, created = Payment.objects.get_or_create(
        order=order,
        provider=provider_value,
        transaction_id=transaction_id,
        defaults={
            "amount": amount,
            "status": status_value,
            "payload": payload or {},
        },
    )
    if not created:
        payment.amount = amount
        payment.status = status_value
        payment.payload = payload or {}
        payment.save(update_fields=["amount", "status", "payload"])

    if status_value == Payment.Status.COMPLETED:
        order.status = Order.Status.PAID
        order.save(update_fields=["status"])
        send_order_receipt_email.delay(order.id)
    else:
        order.status = Order.Status.PENDING
        order.save(update_fields=["status"])
    return payment


def initiate_payment(order: Order, method: str):
    method = (method or "").lower()
    if method == Payment.Provider.STRIPE:
        intent = create_stripe_payment_intent(order)
        if not intent:
            raise ValueError("Stripe is not configured.")
        record_payment(
            order,
            Payment.Provider.STRIPE,
            order.total,
            Payment.Status.PENDING,
            intent["id"],
            intent,
        )
        return {
            "provider": "stripe",
            "client_secret": intent["client_secret"],
            "publishable_key": settings.PAYMENT_GATEWAYS.get("stripe", {}).get("public_key", ""),
            "payment_intent": intent["id"],
        }
    if method == Payment.Provider.RAZORPAY:
        razorpay_order = create_razorpay_order(order)
        if not razorpay_order:
            raise ValueError("Razorpay is not configured.")
        record_payment(
            order,
            Payment.Provider.RAZORPAY,
            order.total,
            Payment.Status.PENDING,
            razorpay_order["id"],
            razorpay_order,
        )
        return {
            "provider": "razorpay",
            "order_id": razorpay_order["id"],
            "amount": razorpay_order["amount"],
            "currency": razorpay_order["currency"],
            "key_id": settings.PAYMENT_GATEWAYS.get("razorpay", {}).get("key_id", ""),
        }

    # default COD
    record_payment(
        order,
        Payment.Provider.COD,
        order.total,
        Payment.Status.PENDING,
        f"cod-{order.id}",
        {"note": "Cash on delivery"},
    )
    return {"provider": "cod", "status": "placed"}

