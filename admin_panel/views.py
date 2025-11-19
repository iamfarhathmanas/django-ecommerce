import csv
from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View

from orders.models import Order, OrderItem
from store.models import Product

from .analytics import AnalyticsService


@method_decorator(staff_member_required, name="dispatch")
class DashboardView(TemplateView):
    template_name = "admin_panel/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        days = int(self.request.GET.get("days", 30))

        # Sales overview
        overview = AnalyticsService.get_sales_overview(days=days)
        context.update(overview)

        # Chart data
        context["daily_sales"] = AnalyticsService.get_daily_sales_chart_data(days=days)
        context["category_sales"] = AnalyticsService.get_category_sales_data(days=days)
        context["payment_stats"] = AnalyticsService.get_payment_method_stats(days=days)

        # Top products
        context["top_products"] = AnalyticsService.get_top_products(days=days, limit=10)

        # Customer metrics
        context["customer_metrics"] = AnalyticsService.get_customer_metrics(days=days)

        # Inventory alerts
        context["inventory_alerts"] = AnalyticsService.get_inventory_alerts(threshold=5)

        # Recent orders
        context["recent_orders"] = AnalyticsService.get_recent_orders(limit=10)

        context["days"] = days
        return context


@method_decorator(staff_member_required, name="dispatch")
class ExportOrdersCSVView(View):
    """Export orders to CSV."""

    def get(self, request):
        days = int(request.GET.get("days", 30))
        start_date = timezone.now() - timedelta(days=days)
        orders = Order.objects.filter(created_at__gte=start_date).select_related(
            "user", "shipping_address"
        ).prefetch_related("items")

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="orders_{timezone.now().date()}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Order ID", "Date", "Customer", "Email", "Total", "Status",
            "Payment Method", "Items", "Shipping Address"
        ])

        for order in orders:
            items_str = ", ".join([f"{item.product_title} x{item.quantity}" for item in order.items.all()])
            address = order.shipping_address
            address_str = f"{address.street}, {address.city}, {address.state} {address.postal_code}" if address else "N/A"
            payment = order.payments.first()
            payment_method = payment.provider if payment else "N/A"

            writer.writerow([
                order.id,
                order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                order.user.get_full_name() or order.user.username,
                order.user.email,
                order.total,
                order.status,
                payment_method,
                items_str,
                address_str,
            ])

        return response


@method_decorator(staff_member_required, name="dispatch")
class ExportProductsCSVView(View):
    """Export products to CSV."""

    def get(self, request):
        products = Product.objects.select_related("category").prefetch_related("tags")

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="products_{timezone.now().date()}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "ID", "Title", "Category", "Price", "Stock", "Status",
            "Created At", "Tags"
        ])

        for product in products:
            tags_str = ", ".join([tag.name for tag in product.tags.all()])
            writer.writerow([
                product.id,
                product.title,
                product.category.name if product.category else "Uncategorized",
                product.price,
                product.stock,
                "Published" if product.is_published else "Draft",
                product.created_at.strftime("%Y-%m-%d"),
                tags_str,
            ])

        return response


@method_decorator(staff_member_required, name="dispatch")
class ChartDataAPIView(View):
    """API endpoint for chart data (AJAX)."""

    def get(self, request, chart_type):
        days = int(request.GET.get("days", 30))

        if chart_type == "daily_sales":
            data = AnalyticsService.get_daily_sales_chart_data(days=days)
        elif chart_type == "category_sales":
            data = AnalyticsService.get_category_sales_data(days=days)
        elif chart_type == "payment_methods":
            data = AnalyticsService.get_payment_method_stats(days=days)
        else:
            return JsonResponse({"error": "Invalid chart type"}, status=400)

        return JsonResponse(data)
