from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from store.models import Product

from .services import get_cart, get_wishlist


class CartDetailView(TemplateView):
    template_name = "cart/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_cart(self.request)
        context["cart"] = cart
        context["items"] = cart.items.select_related("product")
        return context


class AddToCartView(View):
    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, pk=kwargs["pk"])
        cart = get_cart(request)
        cart.add_item(product, int(request.POST.get("quantity", 1)))
        if request.headers.get("HX-Request") or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"subtotal": cart.subtotal})
        return redirect("cart:detail")


class UpdateCartItemView(View):
    def post(self, request, *args, **kwargs):
        cart = get_cart(request)
        item = get_object_or_404(cart.items, pk=kwargs["item_id"])
        action = request.POST.get("action")
        if action == "remove":
            item.delete()
        else:
            quantity = int(request.POST.get("quantity", 1))
            if quantity <= 0:
                item.delete()
            else:
                item.quantity = quantity
                item.save(update_fields=["quantity"])
        
        # Check if it's an AJAX request
        if request.headers.get("HX-Request") or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"subtotal": cart.subtotal})
        return redirect("cart:detail")


class WishlistView(TemplateView):
    template_name = "cart/wishlist.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wishlist = get_wishlist(self.request)
        context["wishlist"] = wishlist
        context["items"] = wishlist.items.select_related("product")
        return context


class WishlistToggleView(View):
    def post(self, request, *args, **kwargs):
        wishlist = get_wishlist(request)
        product = get_object_or_404(Product, pk=kwargs["pk"])
        item = wishlist.items.filter(product=product).first()
        if item:
            item.delete()
            exists = False
        else:
            wishlist.items.create(product=product)
            exists = True
        return JsonResponse({"in_wishlist": exists})
