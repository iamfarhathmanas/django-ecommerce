from django.contrib import admin

from .models import Coupon, InventoryLog, Order, OrderEvent, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__email", "tracking_number")
    inlines = [OrderItemInline]


admin.site.register(Coupon)
admin.site.register(Payment)
admin.site.register(InventoryLog)
admin.site.register(OrderEvent)
