from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import Address
from cart.services import get_cart
from .models import Payment
from .serializers import CheckoutSerializer, OrderSerializer
from .services import create_order_from_cart, initiate_payment


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return self.request.user.orders.prefetch_related("items__product")

    @action(detail=False, methods=["post"])
    def checkout(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        address = Address.objects.get(pk=serializer.validated_data["address_id"], user=request.user)
        cart = get_cart(request)
        order = create_order_from_cart(
            request.user,
            address,
            cart,
            serializer.validated_data.get("coupon_code"),
            serializer.validated_data["delivery_fee"],
        )
        payment_method = str(serializer.validated_data.get("payment_method") or Payment.Provider.COD)
        payload = initiate_payment(order, payment_method)
        data = OrderSerializer(order).data
        data["payment"] = payload
        return Response(data, status=status.HTTP_201_CREATED)

