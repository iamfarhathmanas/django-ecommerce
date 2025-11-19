"""
API tests for store endpoints
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Product

User = get_user_model()


class ProductAPITest(APITestCase):
    """Test Product API endpoints."""

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
            description="A test product",
            price=Decimal("99.99"),
            stock=10,
            category=self.category,
            is_published=True,
        )

    def test_list_products(self):
        url = reverse("product-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_product_detail(self):
        url = reverse("product-detail", args=[self.product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test Product")

    def test_product_search(self):
        url = reverse("product-list")
        response = self.client.get(url, {"q": "Test"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_product_suggestions(self):
        url = reverse("product-suggestions")
        response = self.client.get(url, {"q": "Test"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_product_popular_searches(self):
        url = reverse("product-popular-searches")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("queries", response.data)

