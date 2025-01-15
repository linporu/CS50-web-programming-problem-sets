import json
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db.utils import DatabaseError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from network.models import Following, Post

User = get_user_model()


class UserDetailViewTests(TestCase):
    def setUp(self):
        # Create test users
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )
        self.other_user = User.objects.create_user(username="otheruser", password="testpass123")
        self.follower_user = User.objects.create_user(
            username="followeruser", password="testpass123"
        )

        # Create test posts
        self.active_post = Post.objects.create(content="Active post", created_by=self.user)
        self.deleted_post = Post.objects.create(
            content="Deleted post", created_by=self.user, is_deleted=True
        )

        # Create follow relationship (follower_user follows user)
        Following.objects.create(follower=self.follower_user, following=self.user)

        self.client = Client()

    def test_get_user_detail_with_authenticated_follower(self):
        """Test user detail retrieval when viewer is a follower"""
        self.client.login(username="followeruser", password="testpass123")

        response = self.client.get(reverse("user_detail", kwargs={"username": self.user.username}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        user_data = data["user"]

        # Verify is_following field
        self.assertTrue(user_data["is_following"])

        # Verify other user data
        self.assertEqual(user_data["username"], self.user.username)
        self.assertEqual(user_data["email"], self.user.email)
        self.assertEqual(user_data["following_count"], 0)
        self.assertEqual(user_data["follower_count"], 1)

    def test_get_user_detail_with_authenticated_non_follower(self):
        """Test user detail retrieval when viewer is not a follower"""
        self.client.login(username="otheruser", password="testpass123")

        response = self.client.get(reverse("user_detail", kwargs={"username": self.user.username}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        user_data = data["user"]

        # Verify is_following field
        self.assertFalse(user_data["is_following"])

    def test_get_user_detail_with_unauthenticated_user(self):
        """Test user detail retrieval when viewer is not authenticated"""
        response = self.client.get(reverse("user_detail", kwargs={"username": self.user.username}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        user_data = data["user"]

        # Verify is_following field
        self.assertFalse(user_data["is_following"])

    def test_get_user_detail_no_posts(self):
        """Test user detail retrieval for user with no posts"""
        # Create new user with no posts
        new_user = User.objects.create_user(
            username="newuser", password="testpass123", email="new@example.com"
        )

        response = self.client.get(reverse("user_detail", kwargs={"username": new_user.username}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsNone(data["posts"])

    def test_get_nonexistent_user(self):
        """Test retrieving non-existent user"""
        response = self.client.get(reverse("user_detail", kwargs={"username": "nonexistent"}))

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "User not found.")

    def test_invalid_http_method(self):
        """Test invalid HTTP methods"""
        invalid_methods = ["POST", "PUT", "PATCH", "DELETE"]

        for method in invalid_methods:
            response = getattr(self.client, method.lower())(
                reverse("user_detail", kwargs={"username": self.user.username})
            )

            self.assertEqual(response.status_code, 405)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Only accept GET methods.")

    def test_database_error_handling(self):
        """Test database error handling"""
        with patch("network.models.User.objects.get") as mock_get:
            mock_get.side_effect = DatabaseError("Database error")

            response = self.client.get(
                reverse("user_detail", kwargs={"username": self.user.username})
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Database operation failed.")

    def test_unexpected_error_handling(self):
        """Test unexpected error handling"""
        with patch("network.models.User.objects.get") as mock_get:
            mock_get.side_effect = Exception("Unexpected error")

            response = self.client.get(
                reverse("user_detail", kwargs={"username": self.user.username})
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Unexpected error: Unexpected error")

    def test_post_ordering(self):
        """Test posts are ordered by creation time descending"""
        # Create posts with different timestamps
        Post.objects.create(
            content="Newer post",
            created_by=self.user,
            created_at=timezone.now() + timedelta(hours=1),
        )

        response = self.client.get(reverse("user_detail", kwargs={"username": self.user.username}))

        data = json.loads(response.content)
        posts = data["posts"]

        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0]["content"], "Newer post")
        self.assertEqual(posts[1]["content"], "Active post")
