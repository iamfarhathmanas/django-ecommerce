#!/bin/bash
# Build script for Render deployment
# Exit on error
set -e

echo "=========================================="
echo "Starting build process..."
echo "=========================================="

echo "Step 1: Installing dependencies..."
pip install -r requirements.txt

echo "Step 2: Collecting static files..."
python manage.py collectstatic --noinput

echo "Step 3: Running database migrations..."
python manage.py migrate --noinput

echo "Step 4: Creating superuser (if needed)..."
python manage.py create_superuser_if_not_exists || echo "Superuser creation skipped or failed"

echo "Step 5: Seeding products (optional)..."
python manage.py seed_products --count=50 || echo "Product seeding skipped or failed"

echo "=========================================="
echo "Build complete! Ready to start server."
echo "=========================================="

