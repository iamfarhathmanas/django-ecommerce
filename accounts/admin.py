from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Address, OneTimePassword, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Commerce",
            {
                "fields": (
                    "phone_number",
                    "is_phone_verified",
                    "marketing_opt_in",
                    "avatar",
                    "default_currency",
                    "date_of_birth",
                )
            },
        ),
    )
    list_display = ("email", "username", "phone_number", "is_staff", "is_phone_verified")
    search_fields = ("email", "phone_number", "username")
    ordering = ("email",)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "full_name",
        "city",
        "postal_code",
        "country",
        "address_type",
        "is_default",
    )
    list_filter = ("address_type", "country", "is_default")
    search_fields = ("full_name", "city", "postal_code")


@admin.register(OneTimePassword)
class OneTimePasswordAdmin(admin.ModelAdmin):
    list_display = ("user", "purpose", "code", "is_used", "expires_at")
    list_filter = ("purpose", "is_used")
