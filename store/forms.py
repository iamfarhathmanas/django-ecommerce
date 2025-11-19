from django import forms

from .models import Review


class ProductFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Search")
    category = forms.CharField(required=False)
    min_price = forms.DecimalField(required=False)
    max_price = forms.DecimalField(required=False)
    ordering = forms.ChoiceField(
        required=False,
        choices=(
            ("-created_at", "Latest"),
            ("price", "Price: Low to High"),
            ("-price", "Price: High to Low"),
            ("-is_trending", "Trending"),
        ),
    )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "headline", "body")

