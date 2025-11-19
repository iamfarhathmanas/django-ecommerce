from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from accounts.models import Address
from cart.services import get_cart
from .models import Order, Payment
from .services import create_order_from_cart, initiate_payment, record_payment


class CheckoutView(LoginRequiredMixin, TemplateView):
    template_name = "orders/checkout.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["addresses"] = self.request.user.addresses.all()
        context["cart"] = get_cart(self.request)
        context["stripe_public_key"] = settings.PAYMENT_GATEWAYS.get("stripe", {}).get("public_key", "")
        context["razorpay_key_id"] = settings.PAYMENT_GATEWAYS.get("razorpay", {}).get("key_id", "")
        return context

    def post(self, request, *args, **kwargs):
        cart = get_cart(request)
        address_id = request.POST.get("address_id")
        coupon_code = request.POST.get("coupon_code")
        delivery_fee = Decimal(request.POST.get("delivery_fee") or 0)
        payment_method = request.POST.get("payment_method", Payment.Provider.COD)
        address = Address.objects.get(pk=address_id, user=request.user)
        try:
            order = create_order_from_cart(request.user, address, cart, coupon_code, delivery_fee)
            payment_payload = initiate_payment(order, payment_method)
        except ValueError as exc:
            messages.error(request, str(exc))
            return self.get(request, *args, **kwargs)

        return JsonResponse({"order_id": order.id, "total": order.total, **payment_payload})


class OrderListView(LoginRequiredMixin, ListView):
    template_name = "orders/order_list.html"
    paginate_by = 10

    def get_queryset(self):
        return self.request.user.orders.prefetch_related("items__product")


class OrderDetailView(LoginRequiredMixin, DetailView):
    template_name = "orders/order_detail.html"
    model = Order

    def get_queryset(self):
        return self.request.user.orders.prefetch_related("items__product", "events")


class PaymentWebhookView(View):
    def post(self, request, provider, *args, **kwargs):
        provider = provider.lower()
        payload = request.body
        if provider == "stripe":
            from .payment_gateways import verify_stripe_event

            event = verify_stripe_event(payload, request.META.get("HTTP_STRIPE_SIGNATURE", ""))
            if not event:
                return HttpResponse(status=400)
            intent = event["data"]["object"]
            order_id = intent["metadata"].get("order_id")
            order = Order.objects.filter(id=order_id).first()
            if not order:
                return HttpResponse(status=404)
            amount = Decimal(intent.get("amount_received") or intent["amount"]) / Decimal("100")
            status = (
                Payment.Status.COMPLETED
                if event["type"] == "payment_intent.succeeded"
                else Payment.Status.FAILED
            )
            record_payment(order, Payment.Provider.STRIPE, amount, status, intent["id"], intent)
            return HttpResponse(status=200)

        if provider == "razorpay":
            from .payment_gateways import verify_razorpay_signature

            event = verify_razorpay_signature(payload, request.META.get("HTTP_X_RAZORPAY_SIGNATURE", ""))
            if not event:
                return HttpResponse(status=400)
            notes = event.get("payload", {}).get("payment", {}).get("entity", {}).get("notes", {})
            order_id = notes.get("order_id")
            order = Order.objects.filter(id=order_id).first()
            if not order:
                return HttpResponse(status=404)
            entity = event.get("payload", {}).get("payment", {}).get("entity", {})
            amount = Decimal(entity.get("amount", 0)) / Decimal("100")
            status = (
                Payment.Status.COMPLETED
                if event.get("event") == "payment.captured"
                else Payment.Status.FAILED
            )
            record_payment(order, Payment.Provider.RAZORPAY, amount, status, entity.get("id", ""), event)
            return HttpResponse(status=200)
        return HttpResponse(status=400)
