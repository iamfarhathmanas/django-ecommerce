from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic import DetailView, ListView, View

from .forms import ProductFilterForm, ReviewForm
from .models import Category, Product
from .search_service import SearchService


class StorefrontView(ListView):
    template_name = "store/home.html"
    model = Product
    paginate_by = 12
    context_object_name = "products"

    def get_queryset(self):
        form = ProductFilterForm(self.request.GET)
        if not form.is_valid():
            return Product.objects.filter(is_published=True)
        data = form.cleaned_data
        return SearchService.search_products(
            query=data.get("q", ""),
            category=data.get("category"),
            min_price=data.get("min_price"),
            max_price=data.get("max_price"),
            ordering=data.get("ordering") or "-created_at",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(is_active=True)
        context["filter_form"] = ProductFilterForm(self.request.GET)
        context["trending_products"] = Product.objects.filter(
            is_trending=True, is_published=True
        )[:8]
        return context


class ProductDetailView(DetailView):
    template_name = "store/product_detail.html"
    model = Product
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["review_form"] = ReviewForm()
        context["related_products"] = Product.objects.filter(
            category=self.object.category, is_published=True
        ).exclude(id=self.object.id)[:4]
        return context


class ReviewCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = ReviewForm(request.POST)
        product = Product.objects.get(slug=kwargs["slug"])
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            return JsonResponse({"rating": review.rating}, status=201)
        return JsonResponse({"errors": form.errors}, status=400)


class SearchSuggestionView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get("q", "").strip()
        limit = int(request.GET.get("limit", 5))
        results = SearchService.get_suggestions(query, limit=limit)
        return JsonResponse({"results": results})
