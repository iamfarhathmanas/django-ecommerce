from rest_framework import serializers

from accounts.serializers import AddressSerializer
from store.serializers import ProductSerializer

from .models import Order, OrderItem, Payment


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = OrderItem
        fields = ("id", "product", "product_title", "quantity", "unit_price")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = AddressSerializer()

    class Meta:
        model = Order
        fields = (
            "id",
            "status",
            "subtotal",
            "discount",
            "delivery_fee",
            "total",
            "shipping_address",
            "items",
            "created_at",
        )


class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.IntegerField()
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    delivery_fee = serializers.DecimalField(max_digits=7, decimal_places=2, default=0)
    payment_method = serializers.ChoiceField(
        choices=(
            (Payment.Provider.STRIPE, "Stripe"),
            (Payment.Provider.RAZORPAY, "Razorpay"),
            (Payment.Provider.COD, "Cash on Delivery"),
        ),
        required=False,
    )

