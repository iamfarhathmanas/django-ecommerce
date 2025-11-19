from django.urls import path

from .views import AddToCartView, CartDetailView, UpdateCartItemView, WishlistToggleView, WishlistView

app_name = "cart"

urlpatterns = [
    path("", CartDetailView.as_view(), name="detail"),
    path("add/<int:pk>/", AddToCartView.as_view(), name="add"),
    path("item/<int:item_id>/", UpdateCartItemView.as_view(), name="item"),
    path("wishlist/", WishlistView.as_view(), name="wishlist"),
    path("wishlist/toggle/<int:pk>/", WishlistToggleView.as_view(), name="wishlist_toggle"),
]

