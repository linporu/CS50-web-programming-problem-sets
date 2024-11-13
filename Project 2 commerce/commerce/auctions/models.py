from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Listing(models.Model):
    title = models.CharField(max_length=64)
    description = models.TextField()
    starting_bid = models.FloatField()
    url = models.URLField(max_length=200, blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="listings",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"title: {self.title}, description = {self.description}. starting bid = {self.starting_bid}"
    
