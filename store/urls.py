from django.urls import path

from .views import (
    ProductDetailView,
    ReviewCreateView,
    SearchSuggestionView,
    StorefrontView,
)

app_name = "store"

urlpatterns = [
    path("", StorefrontView.as_view(), name="home"),
    path("search-suggestions/", SearchSuggestionView.as_view(), name="search_suggestions"),
    path("product/<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),
    path(
        "product/<slug:slug>/review/",
        ReviewCreateView.as_view(),
        name="product_review",
    ),
]

