"""
Tests for store app - products, categories, reviews, search
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from .models import Category, Product, Tag, Review
from .search_service import SearchService

User = get_user_model()


class CategoryModelTest(TestCase):
    """Test Category model."""

    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Electronic products",
            is_active=True,
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, "Electronics")
        self.assertEqual(self.category.slug, "electronics")
        self.assertTrue(self.category.is_active)

    def test_category_str(self):
        self.assertEqual(str(self.category), "Electronics")


class ProductModelTest(TestCase):
    """Test Product model."""

    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics", slug="electronics", is_active=True
        )
        self.product = Product.objects.create(
            title="Test Product",
            slug="test-product",
            description="A test product",
            price=Decimal("99.99"),
            stock=10,
            category=self.category,
            is_published=True,
        )

    def test_product_creation(self):
        self.assertEqual(self.product.title, "Test Product")
        self.assertEqual(self.product.price, Decimal("99.99"))
        self.assertEqual(self.product.stock, 10)
        self.assertTrue(self.product.is_published)

    def test_product_str(self):
        self.assertEqual(str(self.product), "Test Product")

    def test_product_discount_price(self):
        self.product.old_price = Decimal("149.99")
        self.product.save()
        discount = self.product.discount_percentage
        self.assertGreater(discount, 0)

    def test_product_in_stock(self):
        self.assertTrue(self.product.in_stock)
        self.product.stock = 0
        self.product.save()
        self.assertFalse(self.product.in_stock)


class ReviewModelTest(TestCase):
    """Test Review model."""

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
            category=self.category,
            is_published=True,
        )

    def test_review_creation(self):
        review = Review.objects.create(
            user=self.user,
            product=self.product,
            rating=5,
            headline="Great product",
            body="Very satisfied with this purchase.",
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.product, self.product)

    def test_product_average_rating(self):
        Review.objects.create(
            user=self.user, product=self.product, rating=5, headline="Great"
        )
        user2 = User.objects.create_user(
            email="user2@example.com", password="testpass123"
        )
        Review.objects.create(
            user=user2, product=self.product, rating=3, headline="Okay"
        )
        avg_rating = self.product.average_rating
        self.assertEqual(avg_rating, 4.0)


class StorefrontViewTest(TestCase):
    """Test storefront views."""

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name="Electronics", slug="electronics", is_active=True
        )
        self.product = Product.objects.create(
            title="Test Product",
            slug="test-product",
            description="A test product",
            price=Decimal("99.99"),
            stock=10,
            category=self.category,
            is_published=True,
        )

    def test_storefront_view(self):
        response = self.client.get(reverse("store:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "store/home.html")
        self.assertIn(self.product, response.context["products"])

    def test_storefront_search(self):
        response = self.client.get(reverse("store:home"), {"q": "Test"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.product, response.context["products"])

    def test_storefront_category_filter(self):
        response = self.client.get(
            reverse("store:home"), {"category": "electronics"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.product, response.context["products"])

    def test_storefront_price_filter(self):
        response = self.client.get(
            reverse("store:home"), {"min_price": "50", "max_price": "150"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.product, response.context["products"])

    def test_product_detail_view(self):
        response = self.client.get(
            reverse("store:product_detail", args=[self.product.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "store/product_detail.html")
        self.assertEqual(response.context["product"], self.product)

    def test_search_suggestions_view(self):
        response = self.client.get(
            reverse("store:search_suggestions"), {"q": "Test"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)


class SearchServiceTest(TestCase):
    """Test search service."""

    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics", slug="electronics", is_active=True
        )
        self.product1 = Product.objects.create(
            title="iPhone 15",
            slug="iphone-15",
            description="Latest iPhone",
            price=Decimal("999.99"),
            stock=10,
            category=self.category,
            is_published=True,
        )
        self.product2 = Product.objects.create(
            title="Samsung Galaxy",
            slug="samsung-galaxy",
            description="Android phone",
            price=Decimal("799.99"),
            stock=5,
            category=self.category,
            is_published=True,
        )

    def test_search_products_by_title(self):
        results = SearchService.search_products(query="iPhone")
        self.assertIn(self.product1, results)
        self.assertNotIn(self.product2, results)

    def test_search_products_by_description(self):
        results = SearchService.search_products(query="Android")
        self.assertIn(self.product2, results)

    def test_search_products_category_filter(self):
        results = SearchService.search_products(
            query="", category="electronics"
        )
        self.assertIn(self.product1, results)
        self.assertIn(self.product2, results)

    def test_search_products_price_filter(self):
        results = SearchService.search_products(
            query="", min_price=800, max_price=1000
        )
        self.assertIn(self.product1, results)
        self.assertNotIn(self.product2, results)

    def test_get_suggestions(self):
        suggestions = SearchService.get_suggestions("iPh")
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["title"], "iPhone 15")

    def test_get_suggestions_empty_query(self):
        suggestions = SearchService.get_suggestions("")
        self.assertEqual(len(suggestions), 0)
