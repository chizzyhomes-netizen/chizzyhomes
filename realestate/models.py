from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class User(AbstractUser):
    ROLE_CHOICES = (
        ("customer", "Customer"),
        ("agent", "Agent"),
    )

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="customer"
    )

    def __str__(self):
        return self.username


class Property(models.Model):

    PROPERTY_TYPES = (
        ("self_contain", "Self Contain"),
        ("single_room", "Single Room"),
        ("shared_apartment", "Shared Apartment"),
        ("room_parlour", "Room & Parlour"),
        ("apartment", "Apartment"),
    )

    STATUS_CHOICES = (
        ("available", "Available"),
        ("rented", "Rented"),
    )

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="properties"
    )

    title = models.CharField(max_length=200)

    property_type = models.CharField(
        max_length=30,
        choices=PROPERTY_TYPES
    )

    description = models.TextField()

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    location = models.CharField(
        max_length=200,
        default="Gidan Kwano, Minna"
    )

    address = models.CharField(
        max_length=255,
        blank=True
    )

    bedrooms = models.PositiveIntegerField(default=1)

    bathrooms = models.PositiveIntegerField(default=1)


    # =========================
    # AMENITIES
    # =========================

    starlink = models.BooleanField(default=False)
    private_transformer = models.BooleanField(default=False)
    water = models.BooleanField(default=False)
    generator = models.BooleanField(default=False)
    solar_power = models.BooleanField(default=False)
    security = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    furnished = models.BooleanField(default=False)
    air_conditioning = models.BooleanField(default=False)
    water_heater = models.BooleanField(default=False)
    kitchen = models.BooleanField(default=False)
    borehole = models.BooleanField(default=False)
    network_coverage = models.BooleanField(default=False)


    # =========================
    # STATUS
    # =========================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class PropertyImage(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="properties/images/")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Restrict uploading more than 4 images per property
        if not self.pk and self.property.images.count() >= 4:
            raise ValidationError("You can only upload a maximum of 4 images for a property.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.property.title}"


class PropertyVideo(models.Model):
    property = models.OneToOneField(
        Property,
        on_delete=models.CASCADE,
        related_name="video"
    )
    video = models.FileField(upload_to="properties/videos/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Video for {self.property.title}"


class PropertyLocation(models.Model):

    ZONE_CHOICES = (
        # Gidan Kwano Zones
        ("gk_main_gate", "Gidan Kwano - Front Of School"),
        ("gk_express_south_west", "Gidan Kwano - Munchbox"),
        ("gk_market_hub", "Gidan Kwano - MM Castle"),
        ("gk_residential_west", "Gidan Kwano - RCF"),
        ("gk_residential_east", "Gidan Kwano - Talba Road"),
        ("gk_express_south_south", "Gidan Kwano - Sambisa Axis"),
        ("gk_express_south", "Gidan Kwano - Living Faith"),
        ("gk_express_north", "Gidan Kwano - RGGC Chapel"),
        ('gk_express_south_west', 'Gidan Kwano - RGGC Chapel'),
        # Dama Zones
        ("dama_north", "Dama - North Campus Axis"),
        ("dama_central", "Dama - Central Village"),
        ("dama_south", "Dama - South Extension"),
        # Gidan Mangoro Zones
        ("gm_main_road", "Gidan Mangoro - Main Road Corridor"),
        ("gm_interior", "Gidan Mangoro - Interior Lodges"),
        ("gm_east", "Gidan Mangoro - East Axis"),
    )

    property = models.OneToOneField(
        Property,
        on_delete=models.CASCADE,
        related_name="location_details"
    )

    zone = models.CharField(
        max_length=50,
        choices=ZONE_CHOICES,
        default="gk_main_gate"
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        default=9.537169
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        default=6.467573
    )

    distance_to_flag = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Calculated distance in meters from closest landmark flag"
    )

    landmark = models.CharField(
        max_length=150,
        blank=True,
        help_text="e.g. Opposite Central Mosque, Near GK Shuttle Park"
    )

    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.property.title} ({self.get_zone_display()})"