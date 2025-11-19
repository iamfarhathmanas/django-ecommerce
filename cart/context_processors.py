from .services import get_cart


def cart_context(request):
    """Add cart information to template context."""
    cart = get_cart(request)
    return {
        "cart": cart,
        "cart_item_count": cart.items.count() if cart else 0,
    }

