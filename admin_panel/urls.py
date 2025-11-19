from django.urls import path

from .views import (
    ChartDataAPIView,
    DashboardView,
    ExportOrdersCSVView,
    ExportProductsCSVView,
)

app_name = "admin_panel"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("export/orders/", ExportOrdersCSVView.as_view(), name="export_orders"),
    path("export/products/", ExportProductsCSVView.as_view(), name="export_products"),
    path("api/chart/<str:chart_type>/", ChartDataAPIView.as_view(), name="chart_data"),
]

