from decimal import Decimal

from django.conf import settings
from django.db import models

from store.models import Product

User = settings.AUTH_USER_MODEL


class Cart(models.Model):
    user = models.ForeignKey(User, related_name="carts", on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"{self.user.email}'s cart"
        return f"Session cart {self.session_key}"

    @property
    def subtotal(self):
        return sum((item.line_total for item in self.items.all()), Decimal("0"))

    def merge_with(self, other: "Cart"):
        for item in other.items.all():
            self.add_item(item.product, item.quantity)
        other.delete()

    def add_item(self, product: Product, quantity: int = 1):
        item, created = CartItem.objects.get_or_create(
            cart=self,
            product=product,
            defaults={"quantity": quantity, "unit_price": product.current_price},
        )
        if not created:
            item.quantity += quantity
            item.unit_price = product.current_price
            item.save(update_fields=["quantity", "unit_price"])
        return item


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "product")

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class Wishlist(models.Model):
    user = models.ForeignKey(User, related_name="wishlists", on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wishlist {self.pk}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("wishlist", "product")
