#!/bin/bash
# Test runner script for the e-commerce project

echo "Running Django tests..."
python manage.py test

echo ""
echo "Running tests with coverage..."
coverage run --source='.' manage.py test
coverage report
coverage html

echo ""
echo "Coverage report generated in htmlcov/index.html"

