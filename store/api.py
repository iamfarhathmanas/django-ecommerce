from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Product
from .serializers import ProductSerializer
from .search_service import SearchService


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_published=True).select_related("category")
    serializer_class = ProductSerializer
    filterset_fields = ("category__slug", "tags__slug", "is_trending")
    search_fields = ("title", "description", "tags__name")
    ordering_fields = ("created_at", "price", "is_trending")
    ordering = ("-created_at",)

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get("q", "").strip()
        category = self.request.query_params.get("category")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        ordering = self.request.query_params.get("ordering", "-created_at")

        # Use enhanced search if query is provided
        if query:
            min_price_float = float(min_price) if min_price else None
            max_price_float = float(max_price) if max_price else None
            return SearchService.search_products(
                query=query,
                category=category,
                min_price=min_price_float,
                max_price=max_price_float,
                ordering=ordering,
            )
        return queryset

    @action(detail=False, methods=["get"])
    def suggestions(self, request):
        """Get search suggestions."""
        query = request.query_params.get("q", "").strip()
        limit = int(request.query_params.get("limit", 5))
        results = SearchService.get_suggestions(query, limit=limit)
        return Response({"results": results})

    @action(detail=False, methods=["get"])
    def popular_searches(self, request):
        """Get popular search queries."""
        limit = int(request.query_params.get("limit", 10))
        results = SearchService.get_popular_searches(limit=limit)
        return Response({"queries": results})

