from .models import Cart, Wishlist


def _ensure_session(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def get_cart(request):
    session_key = _ensure_session(request)
    cart, _ = Cart.objects.get_or_create(
        session_key=session_key, defaults={"user": request.user if request.user.is_authenticated else None}
    )
    if request.user.is_authenticated and cart.user is None:
        existing_user_cart = Cart.objects.filter(user=request.user).exclude(pk=cart.pk).first()
        if existing_user_cart:
            cart.merge_with(existing_user_cart)
        cart.user = request.user
        cart.save(update_fields=["user"])
    return cart


def get_wishlist(request):
    session_key = _ensure_session(request)
    wishlist, _ = Wishlist.objects.get_or_create(
        session_key=session_key, defaults={"user": request.user if request.user.is_authenticated else None}
    )
    if request.user.is_authenticated and wishlist.user is None:
        wishlist.user = request.user
        wishlist.save(update_fields=["user"])
    return wishlist

