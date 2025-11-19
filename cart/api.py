from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from store.models import Product

from .serializers import CartSerializer, WishlistSerializer
from .services import get_cart, get_wishlist


class CartViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        cart = get_cart(request)
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["post"])
    def add(self, request):
        cart = get_cart(request)
        product = Product.objects.get(pk=request.data["product_id"])
        quantity = int(request.data.get("quantity", 1))
        cart.add_item(product, quantity)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def update_item(self, request):
        cart = get_cart(request)
        item_id = request.data["item_id"]
        quantity = int(request.data["quantity"])
        item = cart.items.get(pk=item_id)
        if quantity <= 0:
            item.delete()
        else:
            item.quantity = quantity
            item.save(update_fields=["quantity"])
        return Response(CartSerializer(cart).data)


class WishlistViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        wishlist = get_wishlist(request)
        return Response(WishlistSerializer(wishlist).data)

    @action(detail=False, methods=["post"])
    def toggle(self, request):
        wishlist = get_wishlist(request)
        product = Product.objects.get(pk=request.data["product_id"])
        item = wishlist.items.filter(product=product).first()
        if item:
            item.delete()
        else:
            wishlist.items.create(product=product)
        return Response(WishlistSerializer(wishlist).data)

