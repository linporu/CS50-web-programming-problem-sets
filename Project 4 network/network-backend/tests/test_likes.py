import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import DatabaseError, IntegrityError
from django.test import Client, TestCase
from django.urls import reverse
from network.models import Like, Post

User = get_user_model()


class PostLikeViewTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username="testuser1", password="testpass123")
        self.user2 = User.objects.create_user(username="testuser2", password="testpass123")

        # Create test post
        self.post = Post.objects.create(content="Test post content", created_by=self.user1)

        self.client = Client()

    def test_like_post_success(self):
        """Test successful post like"""
        self.client.login(username="testuser2", password="testpass123")

        response = self.client.post(
            reverse("like", kwargs={"post_id": self.post.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Post liked successfully.")

        # Verify like was created
        self.assertTrue(Like.objects.filter(user=self.user2, post=self.post).exists())

    def test_like_post_unauthenticated(self):
        """Test liking post when not logged in"""
        response = self.client.post(
            reverse("like", kwargs={"post_id": self.post.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "You must be logged in to like posts.")

    def test_like_nonexistent_post(self):
        """Test liking nonexistent post"""
        self.client.login(username="testuser2", password="testpass123")

        response = self.client.post(
            reverse("like", kwargs={"post_id": 99999}), content_type="application/json"
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Post not found.")

    def test_like_already_liked_post(self):
        """Test liking already liked post"""
        self.client.login(username="testuser2", password="testpass123")
        Like.objects.create(user=self.user2, post=self.post)

        response = self.client.post(
            reverse("like", kwargs={"post_id": self.post.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "You have already liked this post.")

    def test_like_post_integrity_error(self):
        """Test integrity error when liking post"""
        self.client.login(username="testuser2", password="testpass123")

        with patch("network.models.Like.objects.create") as mock_create:
            mock_create.side_effect = IntegrityError()

            response = self.client.post(
                reverse("like", kwargs={"post_id": self.post.id}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Data integrity error, please check your input.")

    def test_like_post_validation_error(self):
        """Test validation error when liking post"""
        self.client.login(username="testuser2", password="testpass123")

        with patch("network.models.Like.objects.create") as mock_create:
            mock_create.side_effect = ValidationError("Invalid data")

            response = self.client.post(
                reverse("like", kwargs={"post_id": self.post.id}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Validation error: Invalid data")

    def test_like_post_database_error(self):
        """Test database error when liking post"""
        self.client.login(username="testuser2", password="testpass123")

        with patch("network.models.Like.objects.create") as mock_create:
            mock_create.side_effect = DatabaseError()

            response = self.client.post(
                reverse("like", kwargs={"post_id": self.post.id}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Database operation error, please try again later.")

    def test_like_post_general_error(self):
        """Test general error when liking post"""
        self.client.login(username="testuser2", password="testpass123")

        with patch("network.models.Like.objects.create") as mock_create:
            mock_create.side_effect = Exception("Unexpected error")

            response = self.client.post(
                reverse("like", kwargs={"post_id": self.post.id}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Unexpected error")

    def test_unlike_post_success(self):
        """Test successful post unlike"""
        self.client.login(username="testuser2", password="testpass123")
        Like.objects.create(user=self.user2, post=self.post)

        response = self.client.delete(
            reverse("like", kwargs={"post_id": self.post.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Post unliked successfully.")

        # Verify like was deleted
        self.assertFalse(Like.objects.filter(user=self.user2, post=self.post).exists())

    def test_unlike_not_liked_post(self):
        """Test unliking not liked post"""
        self.client.login(username="testuser2", password="testpass123")

        response = self.client.delete(
            reverse("like", kwargs={"post_id": self.post.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "You have not liked this post.")

    def test_unlike_post_database_error(self):
        """Test database error when unliking post"""
        self.client.login(username="testuser2", password="testpass123")
        Like.objects.create(user=self.user2, post=self.post)

        with patch("network.models.Like.objects.filter") as mock_filter:
            mock_queryset = MagicMock()
            mock_queryset.exists.return_value = True
            mock_queryset.first.return_value = Like(user=self.user2)
            mock_queryset.delete.side_effect = DatabaseError()
            mock_filter.return_value = mock_queryset

            response = self.client.delete(
                reverse("like", kwargs={"post_id": self.post.id}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Database operation error.")

    def test_unlike_post_general_error(self):
        """Test general error when unliking post"""
        self.client.login(username="testuser2", password="testpass123")
        Like.objects.create(user=self.user2, post=self.post)

        with patch("network.models.Like.objects.filter") as mock_filter:
            mock_queryset = MagicMock()
            mock_queryset.exists.return_value = True
            mock_queryset.first.return_value = Like(user=self.user2)
            mock_queryset.delete.side_effect = Exception("Unexpected error")
            mock_filter.return_value = mock_queryset

            response = self.client.delete(
                reverse("like", kwargs={"post_id": self.post.id}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Unexpected error")

    def test_invalid_http_method(self):
        """Test invalid HTTP methods"""
        self.client.login(username="testuser2", password="testpass123")

        for method in ["put", "patch", "get"]:
            response = getattr(self.client, method)(
                reverse("like", kwargs={"post_id": self.post.id}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 405)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Only accept POST and DELETE methods.")
