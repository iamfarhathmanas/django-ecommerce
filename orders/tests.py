"""
Tests for orders app - checkout, payments, coupons, order services
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import Address
from cart.models import Cart, CartItem
from store.models import Category, Product
from .models import Order, OrderItem, Payment, Coupon
from .services import create_order_from_cart, record_payment, initiate_payment

User = get_user_model()


class CouponModelTest(TestCase):
    """Test Coupon model."""

    def setUp(self):
        self.coupon = Coupon.objects.create(
            code="SAVE10",
            discount_type=Coupon.DiscountType.PERCENTAGE,
            discount_value=Decimal("10"),
            min_purchase=Decimal("100"),
            max_discount=Decimal("50"),
            is_active=True,
        )

    def test_coupon_creation(self):
        self.assertEqual(self.coupon.code, "SAVE10")
        self.assertTrue(self.coupon.is_active)

    def test_coupon_apply_percentage(self):
        result = self.coupon.apply(Decimal("200"))
        self.assertEqual(result, Decimal("20"))  # 10% of 200

    def test_coupon_apply_fixed(self):
        coupon = Coupon.objects.create(
            code="FIXED20",
            discount_type=Coupon.DiscountType.FIXED,
            discount_value=Decimal("20"),
            is_active=True,
        )
        result = coupon.apply(Decimal("100"))
        self.assertEqual(result, Decimal("20"))

    def test_coupon_min_purchase(self):
        result = self.coupon.apply(Decimal("50"))  # Below min_purchase
        self.assertEqual(result, Decimal("0"))


class OrderModelTest(TestCase):
    """Test Order model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.address = Address.objects.create(
            user=self.user,
            street="123 Test St",
            city="Test City",
            state="TS",
            postal_code="12345",
            country="US",
        )
        self.category = Category.objects.create(
            name="Electronics", slug="electronics", is_active=True
        )
        self.product = Product.objects.create(
            title="Test Product",
            slug="test-product",
            price=Decimal("99.99"),
            stock=10,
            category=self.category,
            is_published=True,
        )

    def test_order_creation(self):
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            subtotal=Decimal("99.99"),
            total=Decimal("99.99"),
        )
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.subtotal, Decimal("99.99"))

    def test_order_with_coupon(self):
        coupon = Coupon.objects.create(
            code="SAVE10",
            discount_type=Coupon.DiscountType.PERCENTAGE,
            discount_value=Decimal("10"),
            is_active=True,
        )
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            subtotal=Decimal("100"),
            discount=Decimal("10"),
            coupon=coupon,
            total=Decimal("90"),
        )
        self.assertEqual(order.discount, Decimal("10"))
        self.assertEqual(order.total, Decimal("90"))


class OrderServicesTest(TestCase):
    """Test order services."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.address = Address.objects.create(
            user=self.user,
            street="123 Test St",
            city="Test City",
            state="TS",
            postal_code="12345",
            country="US",
        )
        self.category = Category.objects.create(
            name="Electronics", slug="electronics", is_active=True
        )
        self.product = Product.objects.create(
            title="Test Product",
            slug="test-product",
            price=Decimal("99.99"),
            stock=10,
            category=self.category,
            is_published=True,
        )
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            unit_price=self.product.price,
        )

    def test_create_order_from_cart(self):
        order = create_order_from_cart(
            self.user, self.address, self.cart, delivery_fee=Decimal("10")
        )
        self.assertIsNotNone(order)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.subtotal, Decimal("199.98"))
        self.assertEqual(order.total, Decimal("209.98"))

    def test_create_order_with_coupon(self):
        coupon = Coupon.objects.create(
            code="SAVE10",
            discount_type=Coupon.DiscountType.PERCENTAGE,
            discount_value=Decimal("10"),
            is_active=True,
        )
        order = create_order_from_cart(
            self.user, self.address, self.cart, coupon_code="SAVE10"
        )
        self.assertGreater(order.discount, Decimal("0"))
        self.assertLess(order.total, order.subtotal)

    def test_create_order_reduces_stock(self):
        initial_stock = self.product.stock
        order = create_order_from_cart(self.user, self.address, self.cart)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock - 2)

    def test_create_order_out_of_stock(self):
        self.product.stock = 1
        self.product.save()
        with self.assertRaises(ValueError):
            create_order_from_cart(self.user, self.address, self.cart)

    def test_record_payment(self):
        order = create_order_from_cart(self.user, self.address, self.cart)
        payment = record_payment(
            order=order,
            provider=Payment.Provider.STRIPE,
            amount=order.total,
            status=Payment.Status.COMPLETED,
            transaction_id="txn_123",
        )
        self.assertEqual(payment.order, order)
        self.assertEqual(payment.status, Payment.Status.COMPLETED)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)


class OrderViewsTest(TestCase):
    """Test order views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.client.login(email="test@example.com", password="testpass123")
        self.address = Address.objects.create(
            user=self.user,
            street="123 Test St",
            city="Test City",
            state="TS",
            postal_code="12345",
            country="US",
        )
        self.category = Category.objects.create(
            name="Electronics", slug="electronics", is_active=True
        )
        self.product = Product.objects.create(
            title="Test Product",
            slug="test-product",
            price=Decimal("99.99"),
            stock=10,
            category=self.category,
            is_published=True,
        )
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1,
            unit_price=self.product.price,
        )

    def test_checkout_view_get(self):
        response = self.client.get(reverse("orders:checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "orders/checkout.html")

    def test_checkout_view_post_cod(self):
        response = self.client.post(
            reverse("orders:checkout"),
            {
                "address_id": self.address.id,
                "payment_method": Payment.Provider.COD,
                "delivery_fee": "10",
            },
        )
        self.assertEqual(response.status_code, 200)  # JSON response
        self.assertTrue(Order.objects.filter(user=self.user).exists())

    def test_order_list_view(self):
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            subtotal=Decimal("99.99"),
            total=Decimal("99.99"),
        )
        response = self.client.get(reverse("orders:list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(order, response.context["order_list"])

    def test_order_detail_view(self):
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            subtotal=Decimal("99.99"),
            total=Decimal("99.99"),
        )
        response = self.client.get(reverse("orders:detail", args=[order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["order"], order)
