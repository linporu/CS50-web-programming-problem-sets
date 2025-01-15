import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import DatabaseError, IntegrityError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from network.models import Following, Post

User = get_user_model()


class FollowViewTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username="testuser1", password="testpass123")
        self.user2 = User.objects.create_user(username="testuser2", password="testpass123")
        self.client = Client()

    def test_follow_success(self):
        """Test successful follow"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.post(
            reverse("follow", kwargs={"username": "testuser2"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Follow user successfully.")

        # Verify following relationship exists
        self.assertTrue(
            Following.objects.filter(follower=self.user1, following=self.user2).exists()
        )

        # Verify follower/following counts
        self.assertEqual(data["data"]["following_count"], 1)
        self.assertEqual(data["data"]["target_user_followers"], 1)

    def test_follow_unauthenticated(self):
        """Test following when user is not logged in"""
        response = self.client.post(
            reverse("follow", kwargs={"username": "testuser2"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(
            data["error"],
            "You must be logged in to view following posts, follow/unfollow users.",
        )

    def test_follow_nonexistent_user(self):
        """Test following a user that doesn't exist"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.post(
            reverse("follow", kwargs={"username": "nonexistent"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "User not found.")

    def test_follow_self(self):
        """Test attempting to follow oneself"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.post(
            reverse("follow", kwargs={"username": "testuser1"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "You can not follow/unfollow yourself.")

    def test_follow_already_following(self):
        """Test following a user that's already being followed"""
        self.client.login(username="testuser1", password="testpass123")

        # Create initial following relationship
        Following.objects.create(follower=self.user1, following=self.user2)

        response = self.client.post(
            reverse("follow", kwargs={"username": "testuser2"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "You are already following this user.")

    def test_follow_integrity_error(self):
        """Test integrity error when following user"""
        self.client.login(username="testuser1", password="testpass123")

        with patch("network.models.Following.objects.create") as mock_create:
            mock_create.side_effect = IntegrityError("Integrity error")

            response = self.client.post(
                reverse("follow", kwargs={"username": "testuser2"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Data integrity error, please check your input.")

    def test_follow_validation_error(self):
        """Test validation error when following user"""
        self.client.login(username="testuser1", password="testpass123")

        with patch("network.models.Following.objects.create") as mock_create:
            mock_create.side_effect = ValidationError("Validation error")

            response = self.client.post(
                reverse("follow", kwargs={"username": "testuser2"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Validation error: Validation error")

    def test_follow_database_error(self):
        """Test database error when following user"""
        self.client.login(username="testuser1", password="testpass123")

        with patch("network.models.Following.objects.create") as mock_create:
            mock_create.side_effect = DatabaseError("Database error")

            response = self.client.post(
                reverse("follow", kwargs={"username": "testuser2"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Database operation error, please try again later.")

    def test_follow_unexpected_error(self):
        """Test unexpected error when following user"""
        self.client.login(username="testuser1", password="testpass123")

        with patch("network.models.Following.objects.create") as mock_create:
            mock_create.side_effect = Exception("Unexpected error")

            response = self.client.post(
                reverse("follow", kwargs={"username": "testuser2"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Unexpected error")

    def test_unfollow_success(self):
        """Test successful unfollow"""
        self.client.login(username="testuser1", password="testpass123")

        # Create initial following relationship
        Following.objects.create(follower=self.user1, following=self.user2)

        response = self.client.delete(
            reverse("follow", kwargs={"username": "testuser2"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Unfollow user successfully.")

        # Verify following relationship is removed
        self.assertFalse(
            Following.objects.filter(follower=self.user1, following=self.user2).exists()
        )

        # Verify follower/following counts
        self.assertEqual(data["data"]["following_count"], 0)
        self.assertEqual(data["data"]["target_user_followers"], 0)

    def test_unfollow_not_following(self):
        """Test unfollowing a user that's not being followed"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.delete(
            reverse("follow", kwargs={"username": "testuser2"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "You are not following this user.")

    def test_unfollow_database_error(self):
        """Test database error when unfollowing user"""
        self.client.login(username="testuser1", password="testpass123")

        # Create initial following relationship
        Following.objects.create(follower=self.user1, following=self.user2)

        with patch("network.models.Following.objects.filter") as mock_filter:
            mock_queryset = MagicMock()
            mock_queryset.exists.return_value = True
            mock_queryset.delete.side_effect = DatabaseError()
            mock_filter.return_value = mock_queryset

            response = self.client.delete(
                reverse("follow", kwargs={"username": "testuser2"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Database operation error, please try again later.")

            # Verify following relationship still exists
            self.assertTrue(
                Following.objects.filter(follower=self.user1, following=self.user2).exists()
            )

    def test_unfollow_unexpected_error(self):
        """Test unexpected error when unfollowing user"""
        self.client.login(username="testuser1", password="testpass123")

        # Create initial following relationship
        Following.objects.create(follower=self.user1, following=self.user2)

        with patch("network.models.Following.objects.filter") as mock_filter:
            mock_queryset = MagicMock()
            mock_queryset.exists.return_value = True
            mock_queryset.delete.side_effect = Exception("Unexpected error")
            mock_filter.return_value = mock_queryset

            response = self.client.delete(
                reverse("follow", kwargs={"username": "testuser2"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], str(mock_queryset.delete.side_effect))

    def test_invalid_http_method(self):
        """Test invalid HTTP methods"""
        self.client.login(username="testuser1", password="testpass123")

        invalid_methods = ["PUT", "PATCH", "GET"]

        for method in invalid_methods:
            response = getattr(self.client, method.lower())(
                reverse("follow", kwargs={"username": "testuser2"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Only accept POST and DELETE method.")


class PostsFollowingViewTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username="testuser1", password="testpass123")
        self.user2 = User.objects.create_user(username="testuser2", password="testpass123")
        self.user3 = User.objects.create_user(username="testuser3", password="testpass123")

        # Create test posts
        self.post1 = Post.objects.create(content="Test post 1 by user2", created_by=self.user2)
        self.post2 = Post.objects.create(
            content="Test post 2 by user2",
            created_by=self.user2,
            is_deleted=True,  # Deleted post
        )
        self.post3 = Post.objects.create(content="Test post by user3", created_by=self.user3)

        # Create following relationships
        Following.objects.create(follower=self.user1, following=self.user2)

        self.client = Client()

    def test_get_following_posts_success(self):
        """Test successful retrieval of following posts"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.get(reverse("posts_following"))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Verify response format
        self.assertEqual(data["message"], "Get following posts successfully.")
        self.assertIn("posts", data)

        # Should only get non-deleted posts from followed users
        posts = data["posts"]
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["content"], "Test post 1 by user2")

    def test_get_following_posts_unauthenticated(self):
        """Test getting following posts when user is not logged in"""
        response = self.client.get(reverse("posts_following"))

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(
            data["error"],
            "You must be logged in to view following posts, follow/unfollow users.",
        )

    def test_get_following_posts_no_following(self):
        """Test getting following posts when user follows no one"""
        # Create new user with no followings
        User.objects.create_user(username="testuser4", password="testpass123")
        self.client.login(username="testuser4", password="testpass123")

        response = self.client.get(reverse("posts_following"))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data["posts"]), 0)

    def test_get_following_posts_ordering(self):
        """Test that following posts are ordered by creation time"""
        self.client.login(username="testuser1", password="testpass123")

        # Create newer post by followed user
        Post.objects.create(
            content="Newer post by user2",
            created_by=self.user2,
            created_at=timezone.now() + timedelta(hours=1),
        )

        response = self.client.get(reverse("posts_following"))

        data = json.loads(response.content)
        posts = data["posts"]

        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0]["content"], "Newer post by user2")
        self.assertEqual(posts[1]["content"], "Test post 1 by user2")

    def test_invalid_http_method(self):
        """Test invalid HTTP methods"""
        self.client.login(username="testuser1", password="testpass123")

        invalid_methods = ["POST", "PUT", "PATCH", "DELETE"]

        for method in invalid_methods:
            response = getattr(self.client, method.lower())(
                reverse("posts_following"), content_type="application/json"
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Only accept GET method.")

    @patch("network.models.Following.objects.filter")
    def test_following_does_not_exist(self, mock_filter):
        """Test handling of Following.DoesNotExist"""
        self.client.login(username="testuser1", password="testpass123")
        mock_filter.side_effect = Following.DoesNotExist()

        response = self.client.get(reverse("posts_following"))

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Following user does not exist.")

    @patch("network.models.Post.objects.select_related")
    def test_post_does_not_exist(self, mock_select_related):
        """Test handling of Post.DoesNotExist"""
        self.client.login(username="testuser1", password="testpass123")
        mock_queryset = mock_select_related.return_value.prefetch_related.return_value
        mock_chain = mock_queryset.filter.return_value.order_by.return_value
        mock_chain.__iter__.side_effect = Post.DoesNotExist()

        response = self.client.get(reverse("posts_following"))

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Following post does not exist.")

    @patch("network.models.Following.objects.filter")
    def test_database_error_handling(self, mock_filter):
        """Test handling of DatabaseError"""
        self.client.login(username="testuser1", password="testpass123")
        mock_filter.side_effect = DatabaseError("Database error")

        response = self.client.get(reverse("posts_following"))

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Database operation error, please try again later.")

    @patch("network.models.Following.objects.filter")
    def test_general_exception_handling(self, mock_filter):
        """Test handling of general exceptions"""
        self.client.login(username="testuser1", password="testpass123")
        mock_filter.side_effect = Exception("Unexpected error")

        response = self.client.get(reverse("posts_following"))

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Unexpected error")
