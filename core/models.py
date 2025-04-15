from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django.utils.text import slugify
from django.utils import timezone
import uuid
import random
import string
from django.contrib.auth.models import User
from decimal import Decimal

CATEGORY_CHOICES = (
    ('fruits', 'Fruits'),
    ('vegetables', 'Vegetables'),
    ('herbs', 'Herbs & Greens'),
    ('microgreens', 'Microgreens'),
    ('seasonal', 'Seasonal Produce'),
    ('organic', 'Organic Produce'),
)


LABEL_CHOICES = (
    ('organic', 'Organic'),
    ('vegan', 'Vegan'),
    ('locally_sourced', 'Locally Sourced'),
    ('freshly_harvested', 'Freshly Harvested'),
    ('seasonal', 'Seasonal Produce'),
    ('farm_fresh', 'Farm Fresh'),
    ('sustainably_farmed', 'Sustainably Farmed'),
    ('zero_waste', 'Zero-Waste Packaging'),
)


class Item(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='organic'  
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labels = models.CharField(max_length=20, choices=LABEL_CHOICES, blank=True)
    image_url = models.CharField(max_length=255, default='https://developers.elementor.com/path/to/placeholder.png')
    description = models.TextField(blank=True) 
    stock = models.PositiveIntegerField(default=0)
    slug = models.SlugField(default='test-product', unique=True)
    farm_location = models.CharField(max_length=100, blank=True)
    carbon_footprint = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.name
    
    def get_abs_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })
    
    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={
            'slug': self.slug
        })
    
    def get_discounted_price(self):
        active_promotions = self.promotions.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )
        if active_promotions.exists():
            promo = active_promotions.first() 
            discount_rate = Decimal(promo.discount_rate)
            discount = self.price * (discount_rate / 100)
            discounted_price = self.price - discount
            return (
                max(discounted_price, Decimal('0.00')).quantize(Decimal('0.01')),
                discount_rate
            )
        return None, None
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) 
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    ordered = models.BooleanField(default=False)
    order_id = models.CharField(max_length=150, null=True, default="XXX")
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)



    def get_active_promotion(self):
        """Returns the active promotion for this item, if any."""
        now = timezone.now()
        return Promotion.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now,
            products=self.item
        ).first()
    
    def get_final_price_per_item(self):
        promo = self.get_active_promotion()
        if promo:
            discount = (promo.discount_rate / Decimal('100')) * self.item.price
            discounted_price = self.item.price - discount
            return discounted_price 
        return self.item.price

    def get_original_price(self):
        """Original total price without discount."""
        return self.item.price * self.quantity
    def get_final_price(self):
        """Total price after applying promotion-based discount"""
        promo = self.get_active_promotion()
        if promo:
            discount = (promo.discount_rate / Decimal('100')) * self.item.price
            discounted_price = self.item.price - discount
            return discounted_price * self.quantity
        return self.get_original_price()

    def get_amount_saved(self):
        return self.get_original_price() - self.get_final_price()
    
    def __str__(self):
        return f"{self.quantity} of {self.item.name}"


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    delivery_instructions = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.address1}, {self.country}"

class Payment(models.Model):
    PAYMENT_CHOICES = (
        ('credit', 'Credit Card'),
        ('debit', 'Debit Card'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    name_on_card = models.CharField(max_length=255)
    card_number = models.CharField(max_length=16)
    expiration = models.CharField(max_length=7)
    cvv = models.CharField(max_length=4)
    
    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.card_number[-4:]}"

class Order(models.Model):
    segment = lambda: ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)

    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)

    ordered_date = models.DateTimeField(blank=True, null=True)
    is_ordered = models.BooleanField(default=False)  # Track order status
    orderstatuses = (
        ('Pending', 'Pending'),
        ('Out For Shipping', 'Out for Shipping'),
        ('Completed', 'Completed')
    )
    status = models.CharField(max_length=150, choices=orderstatuses, default='Pending') # used
    tracking_no = models.CharField(max_length=150, null=True, default=f"{segment()}-{segment()}-{segment()}") # used
    delivery_date = models.DateField(null=True, blank=True)
    delivery_timeslot = models.CharField(max_length=20, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    slug = models.SlugField(default='order', unique=True)
    
    def get_active_promotions(self):
        """Return active promotions that apply to items in the order."""
        now = timezone.now()
        return Promotion.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )

    def calculate_discounts(self, save=False):
        active_promotions = self.get_active_promotions()
        total_discount = Decimal('0.00')
        original_total = Decimal('0.00')
        applied_promotions = []

        for order_item in self.items.all():
            item_total = order_item.item.price * order_item.quantity
            original_total += item_total

            matched_promotion = None
            for promo in active_promotions:
                if order_item.item in promo.products.all():
                    matched_promotion = promo
                    break

            if matched_promotion:
                discount = (matched_promotion.discount_rate / Decimal('100')) * item_total
                total_discount += discount
                applied_promotions.append({
                    'item': order_item.item,
                    'promotion': matched_promotion,
                    'discount': discount
                })

        discounted_total = original_total - total_discount

        return {
            'original_total': original_total,
            'total_discount': total_discount,
            'discounted_total': discounted_total,
            'applied_promotions': applied_promotions
        }

    def get_total_cost(self):
        discount_data = self.calculate_discounts()
        return round(discount_data['discounted_total'], 2)
    
    def get_original_total_cost(self):
        return round(sum(item.item.price * item.quantity for item in self.items.all()), 2)

    def get_total_count(self):
        return sum(item.quantity for item in self.items.all())

    def get_taxes(self):
        tax_rate = Decimal('0.13')  # 13% tax
        total_cost = Decimal(str(self.get_total_cost()))  
        return total_cost * tax_rate
    
    
    def get_final_price(self):
        """Calculate the final price of the order, including discounts, taxes, and the original cost."""
        total_cost = Decimal(str(self.get_total_cost()))
        taxes = self.get_taxes()
        final_price = round(total_cost + taxes, 2)
        return final_price
    
    
    def save(self, *args, **kwargs):
        if self.is_ordered and not self.ordered_date:
            self.ordered_date = timezone.now()
        if not self.slug or self.slug == 'test-order':
            self.slug = uuid.uuid4().hex[:6] 
        super().save(*args, **kwargs)



    @classmethod
    def get_or_create_cart(cls, user):
        order = cls.objects.filter(user=user, is_ordered=False).first()
        if not order:
            order = cls(user=user, is_ordered=False)
            order.slug = uuid.uuid4().hex[:6]
            order.save()
        return order
    
    def remove_item(self, order_item):
        """Helper method to remove an item from the order"""
        self.items.remove(order_item)
        order_item.delete()
        self.save()

    def is_empty(self):
        """Check if the order has any items left"""
        return not self.items.exists()
    
    def __str__(self):
        return self.user.username

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.user.username
    

class Promotion(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10, help_text="Enter as a percentage (e.g. 10.00 for 10%)")
    products = models.ManyToManyField(Item, related_name='promotions')
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.title
    

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)         
    postal_code = models.CharField(max_length=6, blank=True, null=True)    
    phone = models.CharField(max_length=10, blank=True, null=True)

