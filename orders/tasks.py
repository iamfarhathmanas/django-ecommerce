from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Order
from store.models import Product


def _admin_recipients():
    if settings.ALERT_EMAILS:
        return settings.ALERT_EMAILS
    return [settings.DEFAULT_FROM_EMAIL]


@shared_task
def send_order_created_email(order_id: int):
    order = (
        Order.objects.select_related("user", "shipping_address")
        .prefetch_related("items__product")
        .filter(id=order_id)
        .first()
    )
    if not order or not order.user.email:
        return
    context = {"order": order, "app_name": settings.APP_NAME}
    subject = f"{settings.APP_NAME} order #{order.id} received"
    body = render_to_string("emails/order_created.txt", context)
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [order.user.email])


@shared_task
def send_order_receipt_email(order_id: int):
    order = (
        Order.objects.select_related("user", "shipping_address")
        .prefetch_related("items__product")
        .filter(id=order_id)
        .first()
    )
    if not order or not order.user.email:
        return
    context = {"order": order, "app_name": settings.APP_NAME}
    subject = f"{settings.APP_NAME} payment confirmation #{order.id}"
    body = render_to_string("emails/order_paid.txt", context)
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [order.user.email])


@shared_task
def send_low_stock_alert(product_id: int):
    product = Product.objects.filter(id=product_id).first()
    if not product:
        return
    subject = f"[Inventory] {product.title} is running low"
    body = f"{product.title} has {product.stock} units left."
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, _admin_recipients())


@shared_task
def send_low_stock_digest():
    threshold = settings.LOW_STOCK_THRESHOLD
    products = Product.objects.filter(stock__lte=threshold).order_by("stock")
    if not products.exists():
        return
    subject = f"{settings.APP_NAME} low stock digest"
    lines = ["Products below threshold:"]
    for product in products:
        lines.append(f"- {product.title}: {product.stock} units left")
    body = "\n".join(lines)
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, _admin_recipients())

