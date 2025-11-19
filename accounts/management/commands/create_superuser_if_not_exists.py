"""
Management command to create a superuser if it doesn't exist.
Useful for automated deployments where shell access is not available.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()


class Command(BaseCommand):
    help = "Creates a superuser if it does not exist"

    def handle(self, *args, **options):
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "")
        admin_username = os.getenv("ADMIN_USERNAME", "admin")

        if not admin_password:
            self.stdout.write(
                self.style.WARNING(
                    "ADMIN_PASSWORD not set. Skipping superuser creation."
                )
            )
            return

        if User.objects.filter(username=admin_username).exists():
            self.stdout.write(
                self.style.SUCCESS(f'Superuser "{admin_username}" already exists.')
            )
        else:
            try:
                User.objects.create_superuser(
                    username=admin_username, email=admin_email, password=admin_password
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Superuser "{admin_username}" created successfully.'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error creating superuser: {e}")
                )

