from django.db import models


class Category(models.Model):
   name = models.CharField(max_length=100)
   slug = models.SlugField(unique=True)
   def __str__(self):
       return self.name


class Product(models.Model):
   title = models.CharField(max_length=255)
   slug = models.SlugField(unique=True)
   description = models.TextField(blank=True)
   affiliate_url = models.URLField()
   category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
   is_active = models.BooleanField(default=True)
   created = models.DateTimeField(auto_now_add=True)
   updated = models.DateTimeField(auto_now=True)
   def __str__(self):
       return self.title


class Click(models.Model):
   product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="clicks")
   timestamp = models.DateTimeField(auto_now_add=True)
   ip = models.GenericIPAddressField(null=True, blank=True)
   user_agent = models.CharField(max_length=1024, blank=True)


AVAILABILITY_CHOICES = [
    ("InStock", "Op voorraad"),
    ("OutOfStock", "Uitverkocht"),
    ("PreOrder", "Binnenkort beschikbaar"),
    ("BackOrder", "Nabestelling mogelijk"),
    ("Discontinued", "Niet meer leverbaar"),
]


class AffiliateProductState(models.Model):
    """Authoritative runtime source for affiliate maintenance fields.

    Keyed by ``slug`` — the globally unique product identifier from
    ``ALL_PRODUCTS_BY_SLUG`` in products/views.py.  No FK to the existing
    ``Product`` model because that model has zero records; the live catalogue
    lives in products_*.py files.

    After a record exists, the public website uses:
        price           → DB value (overrides Python default)
        availability    → DB value (overrides Python default)
        price_last_checked → DB value only (not in Python files)
    If no record exists, the Python file values are used as-is (fallback).
    """

    slug = models.SlugField(unique=True, max_length=200, db_index=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Actuele prijs in EUR. Leeg = nog niet ingevuld.",
    )
    availability = models.CharField(
        max_length=20, choices=AVAILABILITY_CHOICES, blank=True, default="",
        help_text="Actuele beschikbaarheid. Leeg = nog niet ingevuld.",
    )
    price_last_checked = models.DateField(
        null=True, blank=True,
        help_text="Datum van laatste handmatige verificatie. NULL = nog nooit gecontroleerd.",
    )

    class Meta:
        verbose_name = "Affiliate productstate"
        verbose_name_plural = "Affiliate product maintenance"

    def __str__(self):
        return self.slug
