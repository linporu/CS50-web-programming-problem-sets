from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Listing(models.Model):
    title = models.CharField(max_length=64)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    url = models.URLField(max_length=200, blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="listings",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class ListingState(models.TextChoices):
        ACTIVE = 'ACTIVE'
        CLOSED = 'CLOSED'

    state = models.CharField(
        max_length=10,
        choices=ListingState.choices,
        default=ListingState.ACTIVE
    )

    current_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    categories = models.ManyToManyField('Category', related_name='listings', blank=True)
    
    winning_bidder = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_listings'
    )

    def save(self, *args, **kwargs):
        # If this is a new object (no pk yet)
        if not self.pk:
            self.current_price = self.starting_bid
        super().save(*args, **kwargs)

    def update_price(self, new_price):
        self.current_price = new_price
        self.save()

    def __str__(self):
        return f"title: {self.title}, description = {self.description}. starting bid = {self.starting_bid}"
    

class Bid(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="bids",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    bidder = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bids"
    )
    bid_at = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    content = models.TextField()
    commenter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Category(models.Model):
    name = models.CharField(
        max_length=64,
        unique=True,
        db_index=True
    )
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    

class Watchlist(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="watching_listings"
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="watching_users"
    )

    class Meta:
        # Ensure each user can only have one watchlist item per listing
        unique_together = ['user', 'listing']