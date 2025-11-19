from django.contrib import admin

from .models import Category, Product, ProductImage, Review, Tag


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "price",
        "stock",
        "is_trending",
        "is_published",
    )
    list_filter = ("category", "is_trending", "is_published")
    search_fields = ("title", "sku")
    inlines = [ProductImageInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(Tag)
admin.site.register(Review)
