"""
Tests for admin panel - analytics, dashboard, exports
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from accounts.models import Address
from orders.models import Order, OrderItem, Payment
from store.models import Category, Product
from .analytics import AnalyticsService

User = get_user_model()


class AnalyticsServiceTest(TestCase):
    """Test analytics service."""

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

    def test_get_sales_overview(self):
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            subtotal=Decimal("99.99"),
            total=Decimal("99.99"),
        )
        overview = AnalyticsService.get_sales_overview(days=30)
        self.assertIn("total_sales", overview)
        self.assertIn("order_count", overview)
        self.assertIn("avg_order_value", overview)
        self.assertGreaterEqual(overview["total_sales"], Decimal("0"))

    def test_get_daily_sales_chart_data(self):
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            subtotal=Decimal("99.99"),
            total=Decimal("99.99"),
        )
        data = AnalyticsService.get_daily_sales_chart_data(days=30)
        self.assertIn("labels", data)
        self.assertIn("sales", data)
        self.assertIn("orders", data)
        self.assertIsInstance(data["labels"], list)

    def test_get_category_sales_data(self):
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            subtotal=Decimal("99.99"),
            total=Decimal("99.99"),
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_title=self.product.title,
            quantity=1,
            unit_price=self.product.price,
        )
        data = AnalyticsService.get_category_sales_data(days=30)
        self.assertIn("labels", data)
        self.assertIn("sales", data)

    def test_get_top_products(self):
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            subtotal=Decimal("99.99"),
            total=Decimal("99.99"),
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_title=self.product.title,
            quantity=2,
            unit_price=self.product.price,
        )
        top_products = AnalyticsService.get_top_products(days=30, limit=10)
        self.assertIsInstance(top_products, list)
        if top_products:
            self.assertIn("title", top_products[0])
            self.assertIn("revenue", top_products[0])
            self.assertIn("quantity", top_products[0])

    def test_get_payment_method_stats(self):
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            subtotal=Decimal("99.99"),
            total=Decimal("99.99"),
        )
        Payment.objects.create(
            order=order,
            provider=Payment.Provider.STRIPE,
            amount=order.total,
            status=Payment.Status.COMPLETED,
            transaction_id="txn_123",
        )
        stats = AnalyticsService.get_payment_method_stats(days=30)
        self.assertIn("labels", stats)
        self.assertIn("counts", stats)
        self.assertIn("totals", stats)

    def test_get_customer_metrics(self):
        User.objects.create_user(
            email="newuser@example.com", password="testpass123"
        )
        metrics = AnalyticsService.get_customer_metrics(days=30)
        self.assertIn("new_customers", metrics)
        self.assertIn("repeat_customers", metrics)
        self.assertIn("total_customers", metrics)

    def test_get_inventory_alerts(self):
        low_stock_product = Product.objects.create(
            title="Low Stock Product",
            slug="low-stock-product",
            price=Decimal("49.99"),
            stock=3,
            category=self.category,
            is_published=True,
        )
        alerts = AnalyticsService.get_inventory_alerts(threshold=5)
        self.assertIsInstance(alerts, list)
        product_ids = [a["id"] for a in alerts]
        self.assertIn(low_stock_product.id, product_ids)

    def test_get_recent_orders(self):
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            subtotal=Decimal("99.99"),
            total=Decimal("99.99"),
        )
        recent = AnalyticsService.get_recent_orders(limit=10)
        self.assertIsInstance(recent, list)
        if recent:
            self.assertIn("id", recent[0])
            self.assertIn("user", recent[0])
            self.assertIn("total", recent[0])


class DashboardViewTest(TestCase):
    """Test dashboard views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            is_staff=True,
        )
        self.client.login(email="test@example.com", password="testpass123")

    def test_dashboard_view_requires_staff(self):
        regular_user = User.objects.create_user(
            email="regular@example.com", password="testpass123"
        )
        self.client.login(email="regular@example.com", password="testpass123")
        response = self.client.get(reverse("admin_panel:dashboard"))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_dashboard_view_staff_access(self):
        response = self.client.get(reverse("admin_panel:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_panel/dashboard.html")

    def test_dashboard_view_with_days_parameter(self):
        response = self.client.get(reverse("admin_panel:dashboard"), {"days": "7"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["days"], 7)

    def test_chart_data_api_view(self):
        response = self.client.get(
            reverse("admin_panel:chart_data", args=["daily_sales"]), {"days": "30"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("labels", data)


class ExportViewsTest(TestCase):
    """Test export views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            is_staff=True,
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
        self.order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            subtotal=Decimal("99.99"),
            total=Decimal("99.99"),
        )

    def test_export_orders_csv(self):
        response = self.client.get(reverse("admin_panel:export_orders"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("Order ID", response.content.decode())

    def test_export_products_csv(self):
        response = self.client.get(reverse("admin_panel:export_products"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("ID", response.content.decode())
        self.assertIn("Test Product", response.content.decode())
