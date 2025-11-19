from django.urls import path

from .views import CheckoutView, OrderDetailView, OrderListView, PaymentWebhookView

app_name = "orders"

urlpatterns = [
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("", OrderListView.as_view(), name="list"),
    path("<int:pk>/", OrderDetailView.as_view(), name="detail"),
    path("webhook/<str:provider>/", PaymentWebhookView.as_view(), name="webhook"),
]

