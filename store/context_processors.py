from .models import Category


def storefront(request):
    return {
        "nav_categories": Category.objects.filter(is_active=True, parent__isnull=True)[:8]
    }

