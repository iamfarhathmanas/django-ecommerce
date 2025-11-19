"""
Management command to seed 100 products with images from free image services.
"""
import random
from decimal import Decimal
from io import BytesIO

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from store.models import Category, Product, Tag, ProductImage


class Command(BaseCommand):
    help = "Seed 100 products with images from free image services"

    # Product data with categories
    PRODUCT_DATA = [
        # Electronics
        {
            "category": "Electronics",
            "products": [
                ("iPhone 15 Pro", "Latest iPhone with A17 chip", 999.99, 50),
                ("Samsung Galaxy S24", "Flagship Android smartphone", 899.99, 45),
                ("MacBook Pro 16", "Professional laptop", 2499.99, 30),
                ("Dell XPS 13", "Ultrabook laptop", 1299.99, 40),
                ("iPad Air", "Tablet for work and play", 599.99, 60),
                ("Sony WH-1000XM5", "Noise-cancelling headphones", 399.99, 35),
                ("AirPods Pro", "Wireless earbuds", 249.99, 80),
                ("Samsung 4K TV", "55-inch 4K Smart TV", 799.99, 25),
                ("PlayStation 5", "Gaming console", 499.99, 20),
                ("Xbox Series X", "Next-gen gaming console", 499.99, 22),
                ("Nintendo Switch", "Portable gaming console", 299.99, 40),
                ("Canon EOS R6", "Mirrorless camera", 2499.99, 15),
                ("GoPro Hero 12", "Action camera", 399.99, 30),
                ("Apple Watch Series 9", "Smartwatch", 399.99, 50),
                ("Fitbit Charge 6", "Fitness tracker", 159.99, 60),
            ],
        },
        # Fashion & Clothing
        {
            "category": "Fashion",
            "products": [
                ("Levi's 501 Jeans", "Classic straight-fit jeans", 89.99, 100),
                ("Nike Air Max 270", "Running shoes", 150.99, 80),
                ("Adidas Ultraboost", "Premium running shoes", 180.99, 75),
                ("Ray-Ban Aviator", "Classic sunglasses", 154.99, 50),
                ("Rolex Submariner", "Luxury dive watch", 8999.99, 5),
                ("Gucci Leather Belt", "Designer belt", 450.99, 20),
                ("Zara Blazer", "Formal blazer", 79.99, 60),
                ("H&M T-Shirt", "Cotton t-shirt", 19.99, 200),
                ("North Face Jacket", "Winter jacket", 199.99, 40),
                ("Converse Chuck Taylor", "Classic sneakers", 55.99, 90),
                ("Puma Sports Bra", "Athletic wear", 29.99, 120),
                ("Under Armour Shorts", "Athletic shorts", 34.99, 100),
                ("Calvin Klein Underwear", "Cotton boxer briefs", 24.99, 150),
                ("Tommy Hilfiger Polo", "Classic polo shirt", 69.99, 70),
                ("Ralph Lauren Dress Shirt", "Formal shirt", 89.99, 55),
            ],
        },
        # Home & Kitchen
        {
            "category": "Home & Kitchen",
            "products": [
                ("KitchenAid Stand Mixer", "Professional mixer", 379.99, 30),
                ("Instant Pot Duo", "Pressure cooker", 99.99, 50),
                ("Dyson V15 Vacuum", "Cordless vacuum cleaner", 699.99, 25),
                ("Nespresso Coffee Machine", "Espresso maker", 199.99, 40),
                ("Le Creuset Dutch Oven", "Cast iron cookware", 349.99, 20),
                ("All-Clad Cookware Set", "Stainless steel set", 599.99, 15),
                ("Cuisinart Food Processor", "Kitchen appliance", 179.99, 35),
                ("Vitamix Blender", "High-performance blender", 449.99, 20),
                ("Shark Steam Mop", "Steam cleaning mop", 129.99, 45),
                ("Roomba i7+", "Robot vacuum", 699.99, 18),
                ("Philips Hue Lights", "Smart lighting kit", 199.99, 30),
                ("Nest Thermostat", "Smart thermostat", 249.99, 25),
                ("YETI Tumbler", "Insulated water bottle", 39.99, 100),
                ("OXO Good Grips Set", "Kitchen tools", 49.99, 60),
                ("Bodum French Press", "Coffee maker", 29.99, 80),
            ],
        },
        # Sports & Outdoors
        {
            "category": "Sports & Outdoors",
            "products": [
                ("Yoga Mat Premium", "Non-slip yoga mat", 29.99, 80),
                ("Dumbbell Set 20kg", "Adjustable weights", 149.99, 40),
                ("Bicycle Road Bike", "Lightweight road bike", 899.99, 15),
                ("Trekking Backpack", "60L hiking backpack", 179.99, 30),
                ("Tent 4-Person", "Camping tent", 199.99, 25),
                ("Sleeping Bag", "Cold weather sleeping bag", 89.99, 50),
                ("Golf Club Set", "Complete golf set", 599.99, 12),
                ("Tennis Racket", "Professional racket", 129.99, 35),
                ("Basketball", "Official size basketball", 24.99, 100),
                ("Soccer Ball", "Professional soccer ball", 34.99, 90),
                ("Fishing Rod Combo", "Fishing equipment", 79.99, 40),
                ("Kayak Inflatable", "2-person kayak", 299.99, 20),
                ("Stand Up Paddleboard", "SUP board", 449.99, 18),
                ("Climbing Harness", "Safety harness", 89.99, 30),
                ("Hiking Boots", "Waterproof boots", 149.99, 45),
            ],
        },
        # Books & Media
        {
            "category": "Books",
            "products": [
                ("The Great Gatsby", "Classic novel", 12.99, 200),
                ("1984 by George Orwell", "Dystopian fiction", 14.99, 180),
                ("To Kill a Mockingbird", "Literary classic", 13.99, 190),
                ("Harry Potter Box Set", "Complete series", 89.99, 50),
                ("The Lord of the Rings", "Fantasy trilogy", 39.99, 70),
                ("Kindle Paperwhite", "E-reader", 139.99, 60),
                ("Audible Subscription", "Audiobook service", 14.99, 1000),
                ("Vinyl Record Player", "Turntable", 199.99, 30),
                ("Bluetooth Speaker", "Portable speaker", 79.99, 80),
                ("Noise Cancelling Headphones", "Over-ear headphones", 199.99, 50),
                ("Guitar Acoustic", "6-string guitar", 299.99, 25),
                ("Piano Keyboard", "88-key digital piano", 499.99, 15),
                ("DJ Controller", "Professional DJ setup", 399.99, 20),
                ("Microphone USB", "Recording microphone", 99.99, 40),
                ("Studio Monitor Speakers", "Audio monitors", 299.99, 25),
            ],
        },
        # Beauty & Personal Care
        {
            "category": "Beauty",
            "products": [
                ("L'Oreal Shampoo", "Hair care", 8.99, 200),
                ("Olay Face Moisturizer", "Skincare", 24.99, 150),
                ("Maybelline Mascara", "Makeup", 9.99, 180),
                ("Nivea Body Lotion", "Body care", 12.99, 160),
                ("Gillette Razor", "Men's grooming", 19.99, 120),
                ("Philips Electric Shaver", "Electric razor", 89.99, 60),
                ("Hair Dryer Professional", "Blow dryer", 79.99, 50),
                ("Straightening Iron", "Hair straightener", 49.99, 70),
                ("Perfume Eau de Toilette", "Fragrance", 59.99, 80),
                ("Sunscreen SPF 50", "Sun protection", 14.99, 140),
                ("Face Mask Set", "Skincare masks", 19.99, 100),
                ("Lipstick Set", "Makeup collection", 29.99, 90),
                ("Nail Polish Set", "Manicure kit", 15.99, 110),
                ("Hairbrush Set", "Hair styling tools", 24.99, 95),
                ("Bath Bombs Set", "Bath products", 12.99, 130),
            ],
        },
        # Toys & Games
        {
            "category": "Toys & Games",
            "products": [
                ("LEGO Star Wars Set", "Building blocks", 79.99, 40),
                ("Barbie Dreamhouse", "Dollhouse", 199.99, 20),
                ("Nerf Gun Blaster", "Toy blaster", 29.99, 80),
                ("Board Game Monopoly", "Classic board game", 24.99, 60),
                ("Jigsaw Puzzle 1000pc", "Puzzle game", 19.99, 70),
                ("Remote Control Car", "RC vehicle", 49.99, 50),
                ("Drone with Camera", "Quadcopter drone", 149.99, 25),
                ("Action Figure Set", "Collectible figures", 34.99, 45),
                ("Building Blocks Set", "Educational toy", 39.99, 55),
                ("Art Supplies Kit", "Craft materials", 29.99, 65),
                ("Science Experiment Kit", "STEM toy", 49.99, 40),
                ("Musical Instrument Toy", "Kids' instrument", 24.99, 60),
                ("Play Kitchen Set", "Pretend play", 89.99, 30),
                ("Train Set", "Model train", 129.99, 20),
                ("Robot Toy", "Interactive robot", 79.99, 35),
            ],
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Number of products to create (default: 100)",
        )
        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Skip downloading images",
        )

    def handle(self, *args, **options):
        count = options["count"]
        skip_images = options.get("skip_images", False)

        self.stdout.write(self.style.SUCCESS(f"Starting to seed {count} products..."))

        # Create categories and tags
        categories = {}
        tags = {}

        # Create all categories first
        for cat_data in self.PRODUCT_DATA:
            cat_name = cat_data["category"]
            category, created = Category.objects.get_or_create(
                name=cat_name,
                defaults={
                    "slug": slugify(cat_name),
                    "description": f"{cat_name} products",
                    "is_active": True,
                },
            )
            categories[cat_name] = category
            if created:
                self.stdout.write(f"Created category: {cat_name}")

        # Create common tags
        tag_names = [
            "popular",
            "new",
            "bestseller",
            "sale",
            "premium",
            "eco-friendly",
            "limited",
            "trending",
        ]
        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=tag_name, slug=slugify(tag_name))
            tags[tag_name] = tag

        # Create products
        products_created = 0
        all_products = []

        # Collect all products from all categories
        for cat_data in self.PRODUCT_DATA:
            all_products.extend(cat_data["products"])

        # Shuffle and take up to count
        random.shuffle(all_products)
        products_to_create = all_products[:count]

        for title, description, price, stock in products_to_create:
            # Find category for this product
            category = None
            for cat_data in self.PRODUCT_DATA:
                if (title, description, price, stock) in cat_data["products"]:
                    category = categories[cat_data["category"]]
                    break

            if not category:
                category = list(categories.values())[0]

            slug = slugify(title)
            # Ensure unique slug
            base_slug = slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Generate unique SKU
            sku_base = slug.upper().replace("-", "")[:8]
            sku = sku_base
            sku_counter = 1
            while Product.objects.filter(sku=sku).exists():
                sku = f"{sku_base}{sku_counter:03d}"
                sku_counter += 1

            # Create product
            old_price = None
            if random.random() > 0.7:  # 30% chance of having old_price
                old_price = Decimal(str(price * 1.3))

            product = Product.objects.create(
                title=title,
                slug=slug,
                sku=sku,
                description=description,
                price=Decimal(str(price)),
                old_price=old_price,
                stock=stock,
                category=category,
                is_published=True,
                is_trending=random.random() > 0.8,  # 20% trending
            )

            # Add random tags
            num_tags = random.randint(1, 3)
            product.tags.add(*random.sample(list(tags.values()), num_tags))

            # Download and add images
            if not skip_images:
                try:
                    self.download_product_image(product)
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Failed to download image for {title}: {e}")
                    )

            products_created += 1
            if products_created % 10 == 0:
                self.stdout.write(f"Created {products_created} products...")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully created {products_created} products with images!"
            )
        )

    def download_product_image(self, product):
        """Download image from Unsplash Source API based on product category."""
        # Map categories to Unsplash search terms
        category_keywords = {
            "Electronics": "electronics",
            "Fashion": "fashion",
            "Home & Kitchen": "home",
            "Sports & Outdoors": "sports",
            "Books": "books",
            "Beauty": "beauty",
            "Toys & Games": "toys",
        }

        keyword = category_keywords.get(product.category.name, "product")
        
        # Use Unsplash Source API (free, no API key needed)
        # Format: https://source.unsplash.com/800x600/?{keyword}
        image_url = f"https://source.unsplash.com/800x600/?{keyword}"
        
        # Alternative: Use Picsum Photos if Unsplash doesn't work
        # image_url = f"https://picsum.photos/800/600?random={product.id}"

        try:
            response = requests.get(image_url, timeout=10, allow_redirects=True)
            response.raise_for_status()

            # Get the final image URL (after redirects)
            if response.url != image_url:
                response = requests.get(response.url, timeout=10)
                response.raise_for_status()

            image_content = ContentFile(response.content)
            image_name = f"{product.slug}.jpg"

            # Create ProductImage
            product_image = ProductImage.objects.create(
                product=product,
                image=image_name,
                is_primary=True,
            )
            product_image.image.save(image_name, image_content, save=True)

            # Download 1-2 additional images
            for i in range(random.randint(0, 2)):
                try:
                    alt_image_url = f"https://source.unsplash.com/800x600/?{keyword},{i}"
                    alt_response = requests.get(alt_image_url, timeout=10, allow_redirects=True)
                    alt_response.raise_for_status()
                    
                    if alt_response.url != alt_image_url:
                        alt_response = requests.get(alt_response.url, timeout=10)
                        alt_response.raise_for_status()
                    
                    alt_image_content = ContentFile(alt_response.content)
                    alt_image_name = f"{product.slug}-{i+1}.jpg"
                    
                    alt_product_image = ProductImage.objects.create(
                        product=product,
                        image=alt_image_name,
                        is_primary=False,
                    )
                    alt_product_image.image.save(alt_image_name, alt_image_content, save=True)
                except Exception:
                    pass  # Skip if additional image fails

        except requests.RequestException as e:
            # Fallback to Picsum Photos
            try:
                picsum_url = f"https://picsum.photos/800/600?random={product.id}"
                response = requests.get(picsum_url, timeout=10)
                response.raise_for_status()
                
                image_content = ContentFile(response.content)
                image_name = f"{product.slug}.jpg"
                
                product_image = ProductImage.objects.create(
                    product=product,
                    image=image_name,
                    is_primary=True,
                )
                product_image.image.save(image_name, image_content, save=True)
            except Exception:
                self.stdout.write(
                    self.style.WARNING(f"Could not download image for {product.title}")
                )

