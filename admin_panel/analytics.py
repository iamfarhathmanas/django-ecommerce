"""
Analytics and reporting service for admin dashboard.
"""
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone

from orders.models import Order, OrderItem, Payment
from store.models import Product, Category
from accounts.models import User


class AnalyticsService:
    """Service for aggregating analytics data."""

    @staticmethod
    def get_sales_overview(days: int = 30) -> dict:
        """Get sales overview for the last N days."""
        start_date = timezone.now() - timedelta(days=days)
        orders = Order.objects.filter(created_at__gte=start_date)

        total_sales = orders.aggregate(total=Sum("total"))["total"] or Decimal("0")
        order_count = orders.count()
        avg_order_value = orders.aggregate(avg=Avg("total"))["avg"] or Decimal("0")

        # Compare with previous period
        prev_start = start_date - timedelta(days=days)
        prev_orders = Order.objects.filter(
            created_at__gte=prev_start, created_at__lt=start_date
        )
        prev_total = prev_orders.aggregate(total=Sum("total"))["total"] or Decimal("0")
        prev_count = prev_orders.count()

        sales_growth = (
            ((total_sales - prev_total) / prev_total * 100) if prev_total > 0 else 0
        )
        order_growth = (
            ((order_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
        )

        return {
            "total_sales": total_sales,
            "order_count": order_count,
            "avg_order_value": avg_order_value,
            "sales_growth": sales_growth,
            "order_growth": order_growth,
        }

    @staticmethod
    def get_daily_sales_chart_data(days: int = 30) -> dict:
        """Get daily sales data for charting."""
        from django.db.models.functions import TruncDate
        
        start_date = timezone.now() - timedelta(days=days)
        orders = Order.objects.filter(created_at__gte=start_date).annotate(
            day=TruncDate("created_at")
        ).values("day").annotate(
            total=Sum("total"),
            count=Count("id")
        ).order_by("day")

        labels = []
        sales_data = []
        orders_data = []

        # Fill in all days (including zeros)
        current_date = start_date.date()
        end_date = timezone.now().date()
        orders_dict = {item["day"]: item for item in orders}

        while current_date <= end_date:
            labels.append(current_date.strftime("%Y-%m-%d"))
            day_data = orders_dict.get(current_date)
            sales_data.append(float(day_data["total"]) if day_data else 0)
            orders_data.append(day_data["count"] if day_data else 0)
            current_date += timedelta(days=1)

        return {
            "labels": labels,
            "sales": sales_data,
            "orders": orders_data,
        }

    @staticmethod
    def get_category_sales_data(days: int = 30) -> dict:
        """Get sales by category."""
        start_date = timezone.now() - timedelta(days=days)
        items = OrderItem.objects.filter(
            order__created_at__gte=start_date
        ).values("product__category__name").annotate(
            total=Sum(F("quantity") * F("unit_price")),
            quantity=Sum("quantity"),
            count=Count("id")
        ).order_by("-total")

        labels = []
        sales_data = []
        quantity_data = []

        for item in items[:10]:  # Top 10 categories
            labels.append(item["product__category__name"] or "Uncategorized")
            sales_data.append(float(item["total"] or 0))
            quantity_data.append(item["quantity"] or 0)

        return {
            "labels": labels,
            "sales": sales_data,
            "quantities": quantity_data,
        }

    @staticmethod
    def get_top_products(days: int = 30, limit: int = 10) -> list[dict]:
        """Get top selling products."""
        start_date = timezone.now() - timedelta(days=days)
        items = OrderItem.objects.filter(
            order__created_at__gte=start_date
        ).values(
            "product__id",
            "product__title",
            "product__slug"
        ).annotate(
            total_revenue=Sum(F("quantity") * F("unit_price")),
            total_quantity=Sum("quantity"),
            order_count=Count("order", distinct=True)
        ).order_by("-total_quantity")[:limit]

        return [
            {
                "id": item["product__id"],
                "title": item["product__title"],
                "slug": item["product__slug"],
                "revenue": float(item["total_revenue"] or 0),
                "quantity": item["total_quantity"] or 0,
                "orders": item["order_count"],
            }
            for item in items
        ]

    @staticmethod
    def get_payment_method_stats(days: int = 30) -> dict:
        """Get payment method distribution."""
        start_date = timezone.now() - timedelta(days=days)
        payments = Payment.objects.filter(
            order__created_at__gte=start_date
        ).values("provider").annotate(
            count=Count("id"),
            total=Sum("amount")
        ).order_by("-total")

        labels = []
        counts = []
        totals = []

        for payment in payments:
            labels.append(payment["provider"].title())
            counts.append(payment["count"])
            totals.append(float(payment["total"] or 0))

        return {
            "labels": labels,
            "counts": counts,
            "totals": totals,
        }

    @staticmethod
    def get_customer_metrics(days: int = 30) -> dict:
        """Get customer-related metrics."""
        start_date = timezone.now() - timedelta(days=days)

        # New customers
        new_customers = User.objects.filter(date_joined__gte=start_date).count()

        # Repeat customers
        repeat_customers = User.objects.filter(
            orders__created_at__gte=start_date
        ).annotate(
            order_count=Count("orders")
        ).filter(order_count__gt=1).count()

        # Total customers with orders
        total_customers = User.objects.filter(
            orders__created_at__gte=start_date
        ).distinct().count()

        # Average orders per customer
        avg_orders = (
            Order.objects.filter(created_at__gte=start_date)
            .values("user")
            .annotate(count=Count("id"))
            .aggregate(avg=Avg("count"))["avg"] or 0
        )

        return {
            "new_customers": new_customers,
            "repeat_customers": repeat_customers,
            "total_customers": total_customers,
            "avg_orders_per_customer": round(avg_orders, 2),
        }

    @staticmethod
    def get_inventory_alerts(threshold: int = 5) -> list[dict]:
        """Get low stock alerts."""
        products = Product.objects.filter(
            stock__lte=threshold, is_published=True
        ).order_by("stock")[:20]

        return [
            {
                "id": p.id,
                "title": p.title,
                "slug": p.slug,
                "stock": p.stock,
                "category": p.category.name if p.category else "Uncategorized",
            }
            for p in products
        ]

    @staticmethod
    def get_recent_orders(limit: int = 10) -> list[dict]:
        """Get recent orders with details."""
        orders = Order.objects.select_related(
            "user", "shipping_address"
        ).prefetch_related("items").order_by("-created_at")[:limit]

        return [
            {
                "id": o.id,
                "user": o.user.get_full_name() or o.user.username,
                "email": o.user.email,
                "total": float(o.total),
                "status": o.status,
                "created_at": o.created_at,
                "item_count": o.items.count(),
            }
            for o in orders
        ]

