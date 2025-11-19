"""
Tests for cart app - cart, wishlist, cart services
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from store.models import Category, Product
from .models import Cart, CartItem, Wishlist, WishlistItem
from .services import get_cart, add_to_cart, remove_from_cart, update_cart_item

User = get_user_model()


class CartModelTest(TestCase):
    """Test Cart model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.category = Category.objects.create(
            name="Electronics", slug="electronics", is_active=True
        )
        self.product = Product.objects.create(
            title="Test Product",
            slug="test-product",
            price=Decimal("99.99"),
            stock=10,
            category=self.category,
            is_published=True,
        )

    def test_cart_creation(self):
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(cart.user, self.user)
        self.assertEqual(cart.subtotal, Decimal("0"))

    def test_cart_item_creation(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(
            cart=cart, product=self.product, quantity=2, unit_price=self.product.price
        )
        self.assertEqual(item.cart, cart)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.line_total, Decimal("199.98"))

    def test_cart_subtotal_calculation(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=2, unit_price=self.product.price
        )
        cart.refresh_from_db()
        self.assertEqual(cart.subtotal, Decimal("199.98"))


class CartServicesTest(TestCase):
    """Test cart services."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.client = Client()
        self.client.login(email="test@example.com", password="testpass123")
        self.category = Category.objects.create(
            name="Electronics", slug="electronics", is_active=True
        )
        self.product = Product.objects.create(
            title="Test Product",
            slug="test-product",
            price=Decimal("99.99"),
            stock=10,
            category=self.category,
            is_published=True,
        )

    def test_get_cart_authenticated(self):
        cart = get_cart(self.client.request())
        self.assertIsNotNone(cart)
        self.assertEqual(cart.user, self.user)

    def test_add_to_cart(self):
        request = self.client.request()
        request.user = self.user
        cart = add_to_cart(request, self.product.id, 2)
        self.assertEqual(cart.items.count(), 1)
        item = cart.items.first()
        self.assertEqual(item.quantity, 2)

    def test_add_to_cart_existing_item(self):
        request = self.client.request()
        request.user = self.user
        cart = add_to_cart(request, self.product.id, 2)
        cart = add_to_cart(request, self.product.id, 3)
        self.assertEqual(cart.items.count(), 1)
        item = cart.items.first()
        self.assertEqual(item.quantity, 5)

    def test_remove_from_cart(self):
        request = self.client.request()
        request.user = self.user
        cart = add_to_cart(request, self.product.id, 2)
        remove_from_cart(request, self.product.id)
        cart.refresh_from_db()
        self.assertEqual(cart.items.count(), 0)

    def test_update_cart_item(self):
        request = self.client.request()
        request.user = self.user
        cart = add_to_cart(request, self.product.id, 2)
        update_cart_item(request, self.product.id, 5)
        cart.refresh_from_db()
        item = cart.items.first()
        self.assertEqual(item.quantity, 5)


class CartViewsTest(TestCase):
    """Test cart views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.client.login(email="test@example.com", password="testpass123")
        self.category = Category.objects.create(
            name="Electronics", slug="electronics", is_active=True
        )
        self.product = Product.objects.create(
            title="Test Product",
            slug="test-product",
            price=Decimal("99.99"),
            stock=10,
            category=self.category,
            is_published=True,
        )

    def test_cart_detail_view(self):
        response = self.client.get(reverse("cart:detail"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cart/cart.html")

    def test_add_to_cart_view(self):
        response = self.client.post(
            reverse("cart:add"), {"product_id": self.product.id, "quantity": 2}
        )
        self.assertEqual(response.status_code, 302)  # Redirect
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)

    def test_remove_from_cart_view(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=2, unit_price=self.product.price
        )
        response = self.client.post(
            reverse("cart:remove"), {"product_id": self.product.id}
        )
        self.assertEqual(response.status_code, 302)
        cart.refresh_from_db()
        self.assertEqual(cart.items.count(), 0)


class WishlistModelTest(TestCase):
    """Test Wishlist model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.category = Category.objects.create(
            name="Electronics", slug="electronics", is_active=True
        )
        self.product = Product.objects.create(
            title="Test Product",
            slug="test-product",
            price=Decimal("99.99"),
            stock=10,
            category=self.category,
            is_published=True,
        )

    def test_wishlist_creation(self):
        wishlist = Wishlist.objects.create(user=self.user)
        self.assertEqual(wishlist.user, self.user)

    def test_wishlist_item_creation(self):
        wishlist = Wishlist.objects.create(user=self.user)
        item = WishlistItem.objects.create(wishlist=wishlist, product=self.product)
        self.assertEqual(item.wishlist, wishlist)
        self.assertEqual(item.product, self.product)
