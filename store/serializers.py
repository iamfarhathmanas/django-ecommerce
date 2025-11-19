from rest_framework import serializers

from .models import Category, Product, ProductImage, Review, Tag


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "parent")


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "is_primary", "alt_text")


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Review
        fields = ("id", "user", "rating", "headline", "body", "created_at")


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    images = ProductImageSerializer(many=True)
    reviews = ReviewSerializer(many=True)
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")

    class Meta:
        model = Product
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "price",
            "old_price",
            "stock",
            "discount_percentage",
            "sku",
            "is_trending",
            "category",
            "images",
            "tags",
            "reviews",
        )

