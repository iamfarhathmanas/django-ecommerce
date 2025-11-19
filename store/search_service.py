"""
Enhanced search service with caching and analytics.
Can be extended to use Elasticsearch/Haystack when configured.
"""
import hashlib
import json
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.db.models import Q, QuerySet, Count, F
from django.utils.text import slugify

from .models import Product


class SearchService:
    """Enhanced search with caching, ranking, and analytics."""

    CACHE_TIMEOUT = 300  # 5 minutes
    MAX_SUGGESTIONS = 10
    POPULAR_QUERIES_KEY = "search:popular"
    SEARCH_ANALYTICS_KEY = "search:analytics"

    @classmethod
    def _cache_key(cls, query: str, filters: dict) -> str:
        """Generate cache key for search query."""
        key_data = {"q": query, **filters}
        key_str = json.dumps(key_data, sort_keys=True)
        return f"search:{hashlib.md5(key_str.encode()).hexdigest()}"

    @classmethod
    def _track_query(cls, query: str):
        """Track search query for analytics."""
        if not query or len(query.strip()) < 2:
            return
        query = query.strip().lower()
        cache_key = f"{cls.SEARCH_ANALYTICS_KEY}:{query}"
        cache.incr(cache_key, 1)
        cache.expire(cache_key, 86400 * 30)  # 30 days

    @classmethod
    def _get_popular_queries(cls, limit: int = 10) -> list[str]:
        """Get popular search queries from cache."""
        # This is a simplified version; in production, use Redis sorted sets
        return []

    @classmethod
    def _build_search_queryset(cls, query: str, base_qs: QuerySet) -> QuerySet:
        """Build optimized search queryset with ranking."""
        if not query:
            return base_qs

        query = query.strip()
        if len(query) < 2:
            return base_qs.none()

        # Split query into words
        words = query.split()
        
        # Build Q objects with priority:
        # 1. Exact title match
        # 2. Title contains (all words)
        # 3. Title contains (any word)
        # 4. Description contains
        # 5. Tags match
        
        q_objects = Q()
        
        # Exact title match (highest priority)
        q_objects |= Q(title__iexact=query)
        
        # Title contains all words
        title_all = Q()
        for word in words:
            title_all &= Q(title__icontains=word)
        q_objects |= title_all
        
        # Title contains any word
        title_any = Q()
        for word in words:
            title_any |= Q(title__icontains=word)
        q_objects |= title_any
        
        # Description contains
        desc_q = Q()
        for word in words:
            desc_q |= Q(description__icontains=word)
        q_objects |= desc_q
        
        # Tags match
        tags_q = Q()
        for word in words:
            tags_q |= Q(tags__name__icontains=word)
        q_objects |= tags_q

        results = base_qs.filter(q_objects).distinct()
        
        # Annotate with relevance score (simplified ranking)
        # Products with exact title match get highest score
        results = results.annotate(
            relevance_score=Count(
                "id",
                filter=Q(title__iexact=query)
            ) * 100
            + Count(
                "id",
                filter=Q(title__icontains=query)
            ) * 50
            + Count(
                "id",
                filter=Q(description__icontains=query)
            ) * 10
        )
        
        return results.order_by("-relevance_score", "-is_trending", "-created_at")

    @classmethod
    def search_products(
        cls,
        query: str = "",
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        ordering: str = "-created_at",
        use_cache: bool = True,
    ) -> QuerySet:
        """
        Search products with caching and ranking.
        
        Args:
            query: Search query string
            category: Category slug filter
            min_price: Minimum price filter
            max_price: Maximum price filter
            ordering: Ordering field
            use_cache: Whether to use cache
            
        Returns:
            QuerySet of products
        """
        # Track query for analytics
        if query:
            cls._track_query(query)

        # Build cache key
        filters = {
            "category": category or "",
            "min_price": str(min_price) if min_price else "",
            "max_price": str(max_price) if max_price else "",
            "ordering": ordering,
        }
        cache_key = cls._cache_key(query, filters)

        # Try cache first
        if use_cache:
            cached = cache.get(cache_key)
            if cached is not None:
                # Return queryset from cached IDs
                product_ids = cached
                return Product.objects.filter(id__in=product_ids).order_by(
                    *[f"-{ordering}"] if ordering.startswith("-") else [ordering]
                )

        # Build base queryset
        qs = Product.objects.filter(is_published=True).select_related("category").prefetch_related("tags", "images")

        # Apply search query
        if query:
            qs = cls._build_search_queryset(query, qs)
        else:
            qs = qs.annotate(relevance_score=F("id") * 0)  # No relevance for non-search

        # Apply filters
        if category:
            qs = qs.filter(category__slug=category)
        if min_price is not None:
            qs = qs.filter(price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)

        # Apply ordering (if not already ordered by relevance)
        if not query or ordering != "-relevance_score":
            if ordering.startswith("-"):
                qs = qs.order_by(ordering, "-created_at")
            else:
                qs = qs.order_by(ordering, "-created_at")

        # Cache results (store IDs only)
        if use_cache:
            product_ids = list(qs.values_list("id", flat=True)[:100])  # Limit cache size
            cache.set(cache_key, product_ids, cls.CACHE_TIMEOUT)

        return qs

    @classmethod
    def get_suggestions(cls, query: str, limit: int = 5) -> list[dict]:
        """
        Get search suggestions with fuzzy matching.
        
        Args:
            query: Partial search query
            limit: Maximum number of suggestions
            
        Returns:
            List of suggestion dicts with title, slug, and match type
        """
        if not query or len(query.strip()) < 2:
            return []

        query = query.strip().lower()
        cache_key = f"search:suggestions:{hashlib.md5(query.encode()).hexdigest()}"

        # Try cache
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        # Build suggestions
        suggestions = []
        
        # Exact title matches (highest priority)
        exact_matches = Product.objects.filter(
            title__iexact=query, is_published=True
        ).values("title", "slug")[:limit]
        for item in exact_matches:
            suggestions.append({**item, "match_type": "exact"})

        # Title starts with
        if len(suggestions) < limit:
            starts_with = Product.objects.filter(
                title__istartswith=query, is_published=True
            ).exclude(slug__in=[s["slug"] for s in suggestions]).values("title", "slug")[:limit - len(suggestions)]
            for item in starts_with:
                suggestions.append({**item, "match_type": "starts_with"})

        # Title contains
        if len(suggestions) < limit:
            contains = Product.objects.filter(
                title__icontains=query, is_published=True
            ).exclude(slug__in=[s["slug"] for s in suggestions]).values("title", "slug")[:limit - len(suggestions)]
            for item in contains:
                suggestions.append({**item, "match_type": "contains"})

        # Cache suggestions
        cache.set(cache_key, suggestions, cls.CACHE_TIMEOUT)

        return suggestions

    @classmethod
    def get_popular_searches(cls, limit: int = 10) -> list[str]:
        """Get popular search queries."""
        # Simplified implementation; in production, use Redis sorted sets
        return []

