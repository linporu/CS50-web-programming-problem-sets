from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    
    @property
    def following_count(self):
        return self.following.count()
    
    @property
    def follower_count(self):
        return self.followers.count()


class Post(models.Model):
    CACHE_TIMEOUT = 86400  # 24 hours in seconds

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cached_serialized_data = None
        self._cache_timestamp = None

    content = models.TextField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def comments_count(self):
        return self.comments.filter(is_deleted=False).count()
    
    def clear_cache(self):
        """Clear the cache"""
        self._cached_serialized_data = None
        self._cache_timestamp = None

    def is_cache_valid(self):
        """Check if the cache is still valid"""
        if self._cache_timestamp is None:
            return False
        
        cache_age = timezone.now() - self._cache_timestamp
        return cache_age.total_seconds() < self.CACHE_TIMEOUT

    def serialize(self, force_refresh=False):
        """
        Serialize Post data with cache timeout
        :param force_refresh: Whether to force refresh the cache
        """
        # If force refresh or cache doesn't exist or cache expired
        if (force_refresh or 
            self._cached_serialized_data is None or 
            not self.is_cache_valid()):
            
            self._cached_serialized_data = {
                "id": self.id,
                "content": self.content,
                "created_by": self.created_by.username,
                "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "is_deleted": self.is_deleted,
                "likes_count": self.likes_count,
                "comments": [comment.serialize() for comment in self.comments.all()],
                "comments_count": self.comments_count
            }
            self._cache_timestamp = timezone.now()
            
        return self._cached_serialized_data
    
    def save(self, *args, **kwargs):
        """Clear cache when saving"""
        self.clear_cache()  # Clear cache when data is updated
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']


class Following(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following"
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['follower', 'following']


class Like(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="likes"
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    content = models.TextField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def serialize(self):
        """Serialize comment data"""
        return {
            "id": self.id,
            "content": self.content,
            "created_by": self.created_by.username,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "is_deleted": self.is_deleted
        }

    class Meta:
        ordering = ['created_at']
    