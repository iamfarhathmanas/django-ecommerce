# Ecommerce Website (Django + MySQL + AWS-ready)

A production-ready e-commerce platform with modular Django apps for accounts, storefront, carts, orders, and a custom analytics dashboard. Includes REST APIs (JWT), wishlist/cart merging, rating & review system, coupons, and hooks for Stripe/Razorpay/COD payments. Media uploads are compatible with AWS S3 via `django-storages`, and the codebase is tailored for resume/portfolio use.

## Features

- **Authentication:** Email/phone login, optional OTP flow, address book, profile editor.
- **Storefront:** Category tree, product filters (search, category, price, trending, sorting), review and rating workflow, lazy-loaded images, dark-mode friendly UI.
- **Cart & Wishlist:** Guest carts with auto-merge on login, AJAX-friendly endpoints, REST API for cart/wishlist, wishlist toggles.
- **Checkout & Orders:** Address selection, coupon engine, delivery fee input, stock locking, batch numbers, payment tracking (Stripe/Razorpay/COD), webhook endpoint.
- **Inventory & Alerts:** Stock auto-update, inventory logs, low-stock alerts surfaced on the admin dashboard.
- **Admin Dashboard:** Custom staff dashboard with sales metrics, top products, inventory warnings, recent orders.
- **REST API:** DRF viewsets for products, cart, wishlist, orders, and auth (JWT issuance, profile, addresses, OTP endpoints).
- **Search & Discovery:** Enhanced search with Redis caching, relevance ranking, fuzzy matching, auto-suggest with keyboard navigation, and search analytics tracking. Ready for Elasticsearch/Haystack upgrade.

## Project Structure

```text
accounts/       # Custom user, OTP, address book, auth views + API
store/          # Products, categories, tags, reviews, storefront views, DRF serializers
cart/           # Cart & wishlist models/services/views/API
orders/         # Coupons, orders, payments, checkout service, APIs
admin_panel/    # Staff dashboard
config/         # Django project, settings, celery bootstrap
templates/      # Bootstrap 5 UI (responsive, dark-mode friendly)
static/         # Custom styles
```

## Getting Started

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Seeding Sample Data

To populate the database with 100 sample products with images:

```bash
# Seed 100 products with images from free image services
python manage.py seed_products --count=100

# Seed specific number of products
python manage.py seed_products --count=50

# Seed without downloading images (faster)
python manage.py seed_products --count=100 --skip-images
```

The command creates:
- 7 product categories (Electronics, Fashion, Home & Kitchen, Sports & Outdoors, Books, Beauty, Toys & Games)
- 100 diverse products with realistic names, descriptions, and prices
- Product images downloaded from Unsplash Source API (free, no API key needed)
- Tags and categories automatically assigned
- Some products marked as trending
- Some products with discount prices

### Environment Variables

Create a `.env` file (or set env vars another way) with values like:

```env
APP_NAME=Manas Shop
DJANGO_SECRET_KEY=your-key
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=django.db.backends.mysql
DB_NAME=ecommerce
DB_USER=root
DB_PASSWORD=secret
DB_HOST=127.0.0.1
DB_PORT=3306
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=ap-south-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLIC_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
RAZORPAY_KEY_ID=rzp_xxx
RAZORPAY_KEY_SECRET=secret
RAZORPAY_WEBHOOK_SECRET=whsec_razorpay
CELERY_BROKER_URL=redis://localhost:6379/0
DEFAULT_FROM_EMAIL=no-reply@example.com
ALERT_EMAILS=ops@example.com,lead@example.com
```

## REST API Highlights

- `POST /api/auth/register` – Register + return JWT pair.
- `POST /api/auth/login` – Email/phone login.
- `POST /api/auth/request-otp` & `/verify-otp` – OTP flows.
- `GET/POST /api/auth/addresses` – Address book.
- `GET /api/products/` – Filterable product catalog (search, category, tags, trending).
- `POST /api/cart/add` / `POST /api/cart/update_item` – Cart management.
- `POST /api/orders/checkout` – Create order from cart using address & coupon.

All endpoints use `rest_framework_simplejwt` for authentication (Bearer tokens).

## Payments & Webhooks

- `orders.services.initiate_payment` spins up Stripe PaymentIntents or Razorpay Orders and persists pending `Payment` rows (COD is supported out of the box).
- `/orders/checkout` view + `/api/orders/checkout` endpoint now return payloads (`client_secret` for Stripe, `order_id` for Razorpay) so the frontend can render the official payment widgets.
- `orders.views.PaymentWebhookView` validates Stripe (`/orders/webhook/stripe/`) & Razorpay (`/orders/webhook/razorpay/`) signatures, updates payments, and flips orders to `paid`.
- Extend `Payment.Provider` enum for more gateways.

## Admin Dashboard & Analytics

Visit `/dashboard/` as a staff user to access comprehensive analytics:

### Key Metrics
- **Sales Overview:** Total sales, order count, average order value with period-over-period growth
- **Customer Metrics:** New customers, repeat customers, average orders per customer
- **Time Period Selection:** View data for 7, 30, 90, or 365 days

### Interactive Charts (Chart.js)
- **Daily Sales & Orders:** Line chart showing sales and order trends over time
- **Sales by Category:** Bar chart of revenue by product category
- **Payment Methods:** Doughnut chart showing payment method distribution

### Data Tables
- **Top Products:** Best sellers by quantity, revenue, and order count
- **Recent Orders:** Latest orders with customer details and status
- **Inventory Alerts:** Low-stock products with visual indicators

### CSV Exports
- **Export Orders:** `/dashboard/export/orders/?days=30` – Full order data with customer and item details
- **Export Products:** `/dashboard/export/products/` – Complete product catalog with inventory status

### Analytics Service
The `admin_panel.analytics.AnalyticsService` provides:
- Sales overview with growth calculations
- Daily/weekly/monthly aggregation
- Category and payment method breakdowns
- Customer cohort analysis
- Inventory alert generation

### Background Tasks
Celery workers (`celery -A config worker -l info`) send:
- Order placed + payment confirmation emails
- Instant low-stock alerts
- Daily low-stock digests via Celery beat (`celery -A config beat -l info`)

## Search & Discovery

The enhanced search system (`store.search_service.SearchService`) provides:

- **Relevance Ranking:** Products are ranked by exact title matches, partial matches, description relevance, and tag matches.
- **Redis Caching:** Search results are cached for 5 minutes to improve performance on popular queries.
- **Auto-Suggest:** Real-time suggestions with fuzzy matching (`/search-suggestions/?q=query`):
  - Exact title matches (highest priority)
  - Title starts with query
  - Title contains query
- **Search Analytics:** Tracks popular queries for future improvements.
- **API Endpoints:**
  - `GET /api/products/?q=query` – Enhanced search with ranking
  - `GET /api/products/suggestions/?q=query` – Auto-suggest API
  - `GET /api/products/popular_searches/` – Popular search queries
- **Frontend:** Auto-suggest dropdown with keyboard navigation (arrow keys, enter) and debounced input.

**Upgrade Path:** The `SearchService` can be extended to use Elasticsearch/Haystack by replacing the `_build_search_queryset` method with Elasticsearch queries while maintaining the same API.

## Testing & Quality

The project includes comprehensive test suites for all major components:

### Running Tests

**Django Test Suite:**
```bash
# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test accounts
python manage.py test store
python manage.py test cart
python manage.py test orders
python manage.py test admin_panel

# Run with verbosity
python manage.py test --verbosity=2

# Run specific test class
python manage.py test accounts.tests.UserModelTest
```

**With Coverage:**
```bash
# Using coverage.py
coverage run --source='.' manage.py test
coverage report
coverage html  # Generates HTML report in htmlcov/

# Or use the test runner scripts
./run_tests.sh  # Linux/Mac
run_tests.bat   # Windows
```

**Using pytest:**
```bash
pytest
pytest accounts/
pytest --cov=. --cov-report=html
```

### Test Coverage

The test suite covers:

- **Accounts (`accounts/tests.py`):**
  - User model and authentication
  - Address management
  - OTP generation and verification
  - Login/signup/logout views
  - Profile management

- **Store (`store/tests.py`):**
  - Category and Product models
  - Product search and filtering
  - Review system
  - Search service functionality
  - Storefront views

- **Cart (`cart/tests.py`):**
  - Cart and CartItem models
  - Wishlist functionality
  - Cart services (add, remove, update)
  - Cart views

- **Orders (`orders/tests.py`):**
  - Order and OrderItem models
  - Coupon system
  - Checkout process
  - Payment recording
  - Order services

- **Admin Panel (`admin_panel/tests.py`):**
  - Analytics service methods
  - Dashboard views
  - CSV export functionality
  - Chart data APIs

- **API Tests (`store/api_tests.py`):**
  - Product API endpoints
  - Search and suggestions APIs
  - REST API authentication

### Quality Checks

```bash
# Django system check
python manage.py check

# Check for code style issues (if using flake8/black)
flake8 .
black --check .

# Check migrations
python manage.py makemigrations --check --dry-run
```

### Test Configuration

- `pytest.ini` - Pytest configuration
- `.coveragerc` - Coverage report settings
- Test files follow Django's naming convention (`tests.py`)

### Continuous Integration

The test suite is designed to run in CI/CD pipelines. Example GitHub Actions workflow:

```yaml
- name: Run tests
  run: |
    python manage.py test
    coverage run --source='.' manage.py test
    coverage report
```

## Next Steps / Extensions

- ✅ Stripe/Razorpay payment integration with frontend UI
- ✅ Enhanced search with caching and auto-suggest
- ✅ Celery background tasks for emails and alerts
- Upgrade search to Elasticsearch/Haystack for typo tolerance at scale
- Harden OTP delivery via SMS gateway (Twilio, AWS SNS, etc.)
- Add product recommendations based on search/view history
- Implement search result pagination with infinite scroll

Happy shipping!
