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

    @property
    def current_price(self):
        """Return the current highest bid price for this listing.
        If no bids exist, return the starting bid price."""
        highest_bid = self.bids.order_by('-price').first()
        return highest_bid.price if highest_bid else self.starting_bid

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