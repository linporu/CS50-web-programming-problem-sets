from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import User, Post, Comment, Like, Following
from django.db.utils import IntegrityError
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
import json
from django.db import models
from django.db.utils import DatabaseError
from unittest.mock import patch, MagicMock
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

User = get_user_model()


class AuthenticationViewTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )
        self.client = Client()
        self.register_url = reverse("register")

    def test_register_view_post_success(self):
        """Test successful registration attempt"""
        response = self.client.post(
            self.register_url,
            data=json.dumps({
                "username": "newuser",
                "email": "new@example.com",
                "password": "newpass123",
                "confirmation": "newpass123"
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)

        # Verify response format
        self.assertEqual(data["message"], "Registration successful")
        self.assertIn("user", data)

        # Verify user data
        user_data = data["user"]
        self.assertEqual(user_data["username"], "newuser")
        self.assertEqual(user_data["email"], "new@example.com")
        self.assertEqual(user_data["following_count"], 0)
        self.assertEqual(user_data["follower_count"], 0)

        # Verify user is authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_register_view_post_missing_fields(self):
        """Test registration with missing fields"""
        test_cases = [
            {"username": "", "email": "test@example.com", "password": "pass123", "confirmation": "pass123"},
            {"username": "testuser", "email": "", "password": "pass123", "confirmation": "pass123"},
            {"username": "testuser", "email": "test@example.com", "password": "", "confirmation": "pass123"},
            {"username": "testuser", "email": "test@example.com", "password": "pass123", "confirmation": ""},
            {},  # Missing all fields
        ]

        for test_case in test_cases:
            response = self.client.post(
                self.register_url,
                data=json.dumps(test_case),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "All fields are required.")
            self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_register_view_password_mismatch(self):
        """Test registration with mismatched passwords"""
        response = self.client.post(
            self.register_url,
            data=json.dumps({
                "username": "newuser",
                "email": "new@example.com",
                "password": "pass123",
                "confirmation": "different123"
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Passwords must match.")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_register_view_duplicate_username(self):
        """Test registration with existing username"""
        response = self.client.post(
            self.register_url,
            data=json.dumps({
                "username": "testuser",  # Same as setUp user
                "email": "another@example.com",
                "password": "pass123",
                "confirmation": "pass123"
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Username already taken.")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_register_view_invalid_json(self):
        """Test registration with invalid JSON data"""
        response = self.client.post(
            self.register_url,
            data="invalid json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Invalid JSON data.")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_register_view_wrong_method(self):
        """Test registration with wrong HTTP method"""
        methods = ["GET", "PUT", "PATCH", "DELETE"]

        for method in methods:
            response = self.client.generic(method, self.register_url)

            self.assertEqual(response.status_code, 405)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "POST request required.")
            self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_csrf_view_returns_token(self):
        """Test that csrf view returns a CSRF token"""
        response = self.client.get(reverse("csrf"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("csrfToken", data)
        self.assertIsInstance(data["csrfToken"], str)
        self.assertTrue(len(data["csrfToken"]) > 0)

    def test_csrf_view_accepts_get_only(self):
        """Test that csrf view only accepts GET requests"""
        # Test POST request
        response = self.client.post(reverse("csrf"))
        self.assertEqual(response.status_code, 405)

        # Test PUT request 
        response = self.client.put(reverse("csrf"))
        self.assertEqual(response.status_code, 405)

        # Test DELETE request
        response = self.client.delete(reverse("csrf"))
        self.assertEqual(response.status_code, 405)


class ModelTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username="testuser1", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", password="testpass123"
        )

        # Create test post
        self.post = Post.objects.create(
            content="Test post content", created_by=self.user1
        )

    def test_create_post(self):
        """Test post creation"""
        self.assertEqual(self.post.content, "Test post content")
        self.assertEqual(self.post.created_by, self.user1)
        self.assertFalse(self.post.is_deleted)
        self.assertEqual(self.post.likes_count, 0)
        self.assertEqual(self.post.comments_count, 0)

    def test_create_comment(self):
        """Test comment creation"""
        comment = Comment.objects.create(
            post=self.post, content="Test comment", created_by=self.user2
        )

        self.assertEqual(comment.content, "Test comment")
        self.assertEqual(comment.created_by, self.user2)
        self.assertEqual(self.post.comments_count, 1)
        self.assertFalse(comment.is_deleted)

    def test_like_post(self):
        """Test post like functionality"""
        like = Like.objects.create(user=self.user2, post=self.post)

        self.assertEqual(self.post.likes_count, 1)

        # Test that duplicate likes raise an error
        with self.assertRaises(IntegrityError):
            Like.objects.create(user=self.user2, post=self.post)

    def test_follow_user(self):
        """Test follow functionality"""
        following = Following.objects.create(
            follower=self.user1, following=self.user2  # user1 follows user2
        )

        # Verify follow relationship is created
        self.assertTrue(
            Following.objects.filter(follower=self.user1, following=self.user2).exists()
        )

        # Test that duplicate follows raise an error
        with self.assertRaises(IntegrityError):
            Following.objects.create(follower=self.user1, following=self.user2)

    def test_soft_delete_post(self):
        """Test post soft deletion"""
        self.post.is_deleted = True
        self.post.save()

        # Verify post is marked as deleted
        self.assertTrue(Post.objects.get(id=self.post.id).is_deleted)

    def test_soft_delete_comment(self):
        """Test comment soft deletion"""
        comment = Comment.objects.create(
            post=self.post, content="Test comment", created_by=self.user2
        )

        comment.is_deleted = True
        comment.save()

        # Verify comment is marked as deleted and not counted
        self.assertTrue(Comment.objects.get(id=comment.id).is_deleted)
        self.assertEqual(self.post.comments_count, 0)

    def test_post_ordering(self):
        """Test post ordering"""
        post2 = Post.objects.create(content="Test post 2", created_by=self.user1)

        posts = Post.objects.all()
        self.assertEqual(posts[0], post2)  # Newer post should be first
        self.assertEqual(posts[1], self.post)

    def test_comment_ordering(self):
        """Test comment ordering"""
        comment1 = Comment.objects.create(
            post=self.post, content="First comment", created_by=self.user2
        )

        comment2 = Comment.objects.create(
            post=self.post, content="Second comment", created_by=self.user2
        )

        comments = self.post.comments.all()
        self.assertEqual(comments[0], comment1)  # Earlier comment should be first
        self.assertEqual(comments[1], comment2)

    def test_post_likes_count(self):
        """Test post likes_count property"""
        # Initial count should be 0
        self.assertEqual(self.post.likes_count, 0)

        # Add one like
        Like.objects.create(user=self.user2, post=self.post)
        self.assertEqual(self.post.likes_count, 1)

        # Add another like from different user
        user3 = User.objects.create_user(username="testuser3", password="testpass123")
        Like.objects.create(user=user3, post=self.post)
        self.assertEqual(self.post.likes_count, 2)

        # Remove a like
        Like.objects.filter(user=self.user2, post=self.post).delete()
        self.assertEqual(self.post.likes_count, 1)

    def test_post_comments_count(self):
        """Test post comments_count property"""
        # Initial count should be 0
        self.assertEqual(self.post.comments_count, 0)

        # Add one comment
        comment1 = Comment.objects.create(
            post=self.post, content="Test comment 1", created_by=self.user2
        )
        self.assertEqual(self.post.comments_count, 1)

        # Add another comment
        comment2 = Comment.objects.create(
            post=self.post, content="Test comment 2", created_by=self.user2
        )
        self.assertEqual(self.post.comments_count, 2)

        # Soft delete a comment
        comment1.is_deleted = True
        comment1.save()
        self.assertEqual(self.post.comments_count, 1)

        # Soft delete another comment
        comment2.is_deleted = True
        comment2.save()
        self.assertEqual(self.post.comments_count, 0)

        # Add new comment after soft deletes
        Comment.objects.create(
            post=self.post, content="Test comment 3", created_by=self.user2
        )
        self.assertEqual(self.post.comments_count, 1)

    def test_post_serialize(self):
        """Test the serialize method of Post model"""
        serialized_post = self.post.serialize()

        self.assertEqual(serialized_post["id"], self.post.id)
        self.assertEqual(serialized_post["content"], self.post.content)
        self.assertEqual(serialized_post["created_by"], self.post.created_by.username)
        self.assertEqual(
            serialized_post["created_at"],
            self.post.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.assertEqual(serialized_post["is_deleted"], self.post.is_deleted)

    def test_post_cache_mechanism(self):
        """Test the caching mechanism of Post serialization"""
        # Initial serialization should create cache
        serialized_data1 = self.post.serialize()
        self.assertIsNotNone(self.post._cached_serialized_data)

        # Second serialization should use cache (same object instance)
        serialized_data2 = self.post.serialize()
        self.assertIs(serialized_data1, serialized_data2)  # Verify it's the same object

    def test_post_cache_clearing(self):
        """Test cache clearing when post is updated"""
        # Initial serialization
        self.post.serialize()
        initial_cache = self.post._cached_serialized_data

        # Update post content
        self.post.content = "Updated content"
        self.post.save()

        # Verify cache was cleared
        self.assertIsNone(self.post._cached_serialized_data)

        # Re-serialize
        new_serialized_data = self.post.serialize()
        self.assertNotEqual(initial_cache, new_serialized_data)
        self.assertEqual(new_serialized_data["content"], "Updated content")

    def test_force_refresh_cache(self):
        """Test forcing cache refresh"""
        # Initial serialization
        initial_data = self.post.serialize()

        # Directly modify content (without save())
        self.post.content = "Changed content"

        # Normal serialization will use cache
        cached_data = self.post.serialize()
        self.assertEqual(cached_data["content"], initial_data["content"])

        # Force cache refresh
        refreshed_data = self.post.serialize(force_refresh=True)
        self.assertEqual(refreshed_data["content"], "Changed content")

    def test_clear_cache_method(self):
        """Test the clear_cache method"""
        # Create cache
        self.post.serialize()
        self.assertIsNotNone(self.post._cached_serialized_data)

        # Clear cache
        self.post.clear_cache()
        self.assertIsNone(self.post._cached_serialized_data)

    def test_cache_timeout(self):
        """Test cache timeout mechanism"""
        # Initial serialization
        initial_data = self.post.serialize()
        initial_timestamp = self.post._cache_timestamp

        # Verify cache is valid
        self.assertTrue(self.post.is_cache_valid())

        # Simulate cache about to expire (set time to 24 hours later)
        self.post._cache_timestamp = timezone.now() - timedelta(
            seconds=Post.CACHE_TIMEOUT - 1
        )
        self.assertTrue(self.post.is_cache_valid())  # Not expired yet

        # Simulate expired cache
        self.post._cache_timestamp = timezone.now() - timedelta(
            seconds=Post.CACHE_TIMEOUT + 1
        )
        self.assertFalse(self.post.is_cache_valid())  # Expired

        # Verify cache is regenerated after expiration
        new_data = self.post.serialize()
        self.assertNotEqual(self.post._cache_timestamp, initial_timestamp)

    def test_cache_invalidation_scenarios(self):
        """Test various cache invalidation scenarios"""
        # 1. Initial state
        self.assertIsNone(self.post._cache_timestamp)
        self.assertFalse(self.post.is_cache_valid())

        # 2. Create cache
        self.post.serialize()
        self.assertIsNotNone(self.post._cache_timestamp)
        self.assertTrue(self.post.is_cache_valid())

        # 3. Clear cache
        self.post.clear_cache()
        self.assertIsNone(self.post._cache_timestamp)
        self.assertFalse(self.post.is_cache_valid())

        # 4. Force refresh
        self.post.serialize()
        old_timestamp = self.post._cache_timestamp
        self.post.serialize(force_refresh=True)
        self.assertNotEqual(self.post._cache_timestamp, old_timestamp)

    def test_post_serialize_with_comments(self):
        """Test serialization of post with comments"""
        # Create test comments
        comment1 = Comment.objects.create(
            post=self.post, content="Test comment 1", created_by=self.user2
        )
        comment2 = Comment.objects.create(
            post=self.post,
            content="Test comment 2",
            created_by=self.user2,
            is_deleted=True,  # Deleted comment
        )

        # Serialize post
        serialized_data = self.post.serialize()

        # Verify comment-related data
        self.assertEqual(
            serialized_data["comments_count"], 1
        )  # Only count non-deleted comments
        self.assertEqual(len(serialized_data["comments"]), 2)  # But return all comments

        # Verify comment serialization format
        comments = serialized_data["comments"]
        self.assertTrue(isinstance(comments, list))

        # Verify comment content and format
        for comment in comments:
            self.assertIn("id", comment)
            self.assertIn("content", comment)
            self.assertIn("created_by", comment)
            self.assertIn("created_at", comment)
            self.assertIn("is_deleted", comment)

        # Verify comment order (sorted by creation time)
        self.assertEqual(comments[0]["content"], "Test comment 1")
        self.assertEqual(comments[1]["content"], "Test comment 2")
        self.assertEqual(comments[0]["created_by"], self.user2.username)

    def test_post_serialize_cache_with_new_comment(self):
        """Test cache behavior when adding new comments"""
        # Initial serialization
        initial_data = self.post.serialize()
        initial_comments_count = initial_data["comments_count"]

        # Add new comment
        Comment.objects.create(
            post=self.post, content="New comment", created_by=self.user2
        )

        # Use cached serialized data
        cached_data = self.post.serialize()
        self.assertEqual(cached_data["comments_count"], initial_comments_count)

        # Force cache refresh
        fresh_data = self.post.serialize(force_refresh=True)
        self.assertEqual(fresh_data["comments_count"], initial_comments_count + 1)

    def test_post_serialize_with_deleted_comments(self):
        """Test serialization with soft-deleted comments"""
        # Create active comment
        active_comment = Comment.objects.create(
            post=self.post, content="Active comment", created_by=self.user2
        )

        # Create deleted comment
        deleted_comment = Comment.objects.create(
            post=self.post,
            content="Deleted comment",
            created_by=self.user2,
            is_deleted=True,
        )

        serialized_data = self.post.serialize()

        # Verify comment count only includes active comments
        self.assertEqual(serialized_data["comments_count"], 1)

        # Verify comments list includes all comments
        comments = serialized_data["comments"]
        self.assertEqual(len(comments), 2)

        # Verify comment contents
        comment_contents = [c["content"] for c in comments]
        self.assertIn("Active comment", comment_contents)
        self.assertIn("Deleted comment", comment_contents)

        # Verify comment status
        active_comments = [c for c in comments if not c["is_deleted"]]
        deleted_comments = [c for c in comments if c["is_deleted"]]
        self.assertEqual(len(active_comments), 1)
        self.assertEqual(len(deleted_comments), 1)

    def test_comment_serialize(self):
        """Test the serialize method of Comment model"""
        comment = Comment.objects.create(
            post=self.post, content="Test comment", created_by=self.user2
        )

        serialized_data = comment.serialize()

        # Verify serialization format
        self.assertEqual(serialized_data["id"], comment.id)
        self.assertEqual(serialized_data["content"], "Test comment")
        self.assertEqual(serialized_data["created_by"], self.user2.username)
        self.assertFalse(serialized_data["is_deleted"])
        self.assertTrue("created_at" in serialized_data)


class PostsListViewTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

        # Create test posts
        self.post1 = Post.objects.create(
            content="Test post 1", created_by=self.user, created_at=timezone.now()
        )

        self.post2 = Post.objects.create(
            content="Test post 2",
            created_by=self.user,
            created_at=timezone.now() + timedelta(hours=1),
        )

        # Create a soft-deleted post
        self.deleted_post = Post.objects.create(
            content="Deleted post", created_by=self.user, is_deleted=True
        )

        # Create test client
        self.client = Client()

    def test_get_posts_exclude_deleted(self):
        """Ensure soft-deleted posts are not included in the response"""
        response = self.client.get(reverse("posts"))
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        posts = data["posts"]

        # Check that the number of posts returned is correct (excluding deleted)
        self.assertEqual(len(posts), 2)

        # Ensure the deleted post is not in the response
        post_contents = [post["content"] for post in posts]
        self.assertNotIn("Deleted post", post_contents)

    def test_get_posts_order(self):
        """Ensure posts are returned in reverse chronological order"""
        response = self.client.get(reverse("posts"))
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        posts = data["posts"]

        # Check that posts are ordered from newest to oldest
        self.assertEqual(posts[0]["content"], "Test post 2")
        self.assertEqual(posts[1]["content"], "Test post 1")

    def test_get_posts_response_format(self):
        """Check the response format and message on successful retrieval"""
        response = self.client.get(reverse("posts"))
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        # Verify the structure of the response
        self.assertIn("message", data)
        self.assertIn("posts", data)
        self.assertEqual(data["message"], "Get posts successfully.")

        # Verify the format of each post
        for post in data["posts"]:
            self.assertIn("id", post)
            self.assertIn("content", post)
            self.assertIn("created_by", post)

    @patch("network.models.Post.objects.select_related")
    def test_get_posts_object_does_not_exist(self, mock_select_related):
        """Test handling of Post.DoesNotExist error when getting posts"""
        # Mock the chain of queryset methods
        mock_chain = (
            mock_select_related.return_value.prefetch_related.return_value.filter.return_value.order_by.return_value
        )
        mock_chain.__iter__.side_effect = Post.DoesNotExist("Posts do not exist")

        response = self.client.get(reverse("posts"))

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Posts do not exist.")

    @patch("network.models.Post.objects.select_related")
    def test_get_posts_database_error(self, mock_select_related):
        """Test handling of DatabaseError when getting posts"""
        # Mock the chain of queryset methods
        mock_chain = (
            mock_select_related.return_value.prefetch_related.return_value.filter.return_value.order_by.return_value
        )
        mock_chain.__iter__.side_effect = DatabaseError("Database error")

        response = self.client.get(reverse("posts"))

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertEqual(
            data["error"], "Database operation error, please try again later."
        )

    @patch("network.models.Post.objects.select_related")
    def test_get_posts_general_exception(self, mock_select_related):
        """Test handling of general Exception when getting posts"""
        # Mock the chain of queryset methods
        mock_chain = (
            mock_select_related.return_value.prefetch_related.return_value.filter.return_value.order_by.return_value
        )
        mock_chain.__iter__.side_effect = Exception("Unexpected error")

        response = self.client.get(reverse("posts"))

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Unexpected error")


class PostsCreateViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client = Client()

    def test_create_post_authenticated(self):
        """Test post creation when user is authenticated"""
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(
            reverse("posts"),
            json.dumps({"content": "New test post"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Post created successfully.")
        self.assertTrue(Post.objects.filter(content="New test post").exists())

    def test_create_post_unauthenticated(self):
        """Test post creation when user is not authenticated"""
        response = self.client.post(
            reverse("posts"),
            json.dumps({"content": "New test post"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "You must be logged in to post.")

    def test_create_post_invalid_json(self):
        """Test post creation with invalid JSON data"""
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(
            reverse("posts"), "invalid json", content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Invalid JSON data.")

    def test_create_post_empty_content(self):
        """Test post creation with empty content"""
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(
            reverse("posts"),
            json.dumps({"content": ""}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Post content cannot be empty.")

    @patch("network.models.Post.objects.create")
    def test_create_post_integrity_error(self, mock_create):
        """Test post creation with IntegrityError"""
        mock_create.side_effect = IntegrityError()
        self.client.login(username="testuser", password="testpassword")

        response = self.client.post(
            reverse("posts"),
            json.dumps({"content": "Test post"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(
            data["error"], "Data integrity error, please check your input."
        )

    @patch("network.models.Post.objects.create")
    def test_create_post_validation_error(self, mock_create):
        """Test post creation with ValidationError"""
        mock_create.side_effect = ValidationError("Invalid data")
        self.client.login(username="testuser", password="testpassword")

        response = self.client.post(
            reverse("posts"),
            json.dumps({"content": "Test post"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Validation error: Invalid data")

    @patch("network.models.Post.objects.create")
    def test_create_post_database_error(self, mock_create):
        """Test post creation with DatabaseError"""
        mock_create.side_effect = DatabaseError()
        self.client.login(username="testuser", password="testpassword")

        response = self.client.post(
            reverse("posts"),
            json.dumps({"content": "Test post"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertEqual(
            data["error"], "Database operation error, please try again later."
        )

    @patch("network.models.Post.objects.create")
    def test_create_post_general_exception(self, mock_create):
        """Test post creation with general Exception"""
        mock_create.side_effect = Exception("Unexpected error")
        self.client.login(username="testuser", password="testpassword")

        response = self.client.post(
            reverse("posts"),
            json.dumps({"content": "Test post"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Unexpected error")

    def test_invalid_method(self):
        """Ensure error is returned for invalid HTTP methods"""
        response = self.client.put(reverse("posts"))
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.content)
        self.assertEqual(data["error"], "Only accept GET and POST method.")


class PostDetailViewTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        # Create test post
        self.post = Post.objects.create(
            content="Test post content", created_by=self.user
        )
        self.client = Client()

    def test_get_post_detail_success(self):
        """Test successful retrieval of post details"""
        response = self.client.get(reverse("post", kwargs={"post_id": self.post.id}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Get post successfully.")
        self.assertEqual(data["post"]["content"], "Test post content")
        self.assertEqual(data["post"]["created_by"], "testuser")

    def test_get_deleted_post(self):
        """Test retrieving a deleted post"""
        # Mark post as deleted
        self.post.is_deleted = True
        self.post.save()

        response = self.client.get(reverse("post", kwargs={"post_id": self.post.id}))

        self.assertEqual(response.status_code, 410)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "This post has been deleted by the author.")

    def test_get_nonexistent_post(self):
        """Test retrieving a non-existent post"""
        non_existent_id = 99999
        response = self.client.get(reverse("post", kwargs={"post_id": non_existent_id}))

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Post not found.")

    def test_database_error_handling(self):
        """Test handling of database errors"""
        with patch("network.models.Post.objects.select_related") as mock_select_related:
            # Simulate database error
            mock_select_related.return_value.get.side_effect = DatabaseError()

            response = self.client.get(
                reverse("post", kwargs={"post_id": self.post.id})
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(
                data["error"], "Database operation error, please try again later."
            )

    def test_general_exception_handling(self):
        """Test handling of general exceptions"""
        with patch("network.models.Post.objects.select_related") as mock_select_related:
            # Simulate general exception
            mock_select_related.return_value.get.side_effect = Exception(
                "Unexpected error"
            )

            response = self.client.get(
                reverse("post", kwargs={"post_id": self.post.id})
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Unexpected error")


class PostEditViewTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username="testuser1", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", password="testpass123"
        )

        # Create test post
        self.post = Post.objects.create(
            content="Original content", created_by=self.user1
        )

        self.client = Client()

    def test_edit_post_success(self):
        """Test successful post edit by the owner"""
        self.client.login(username="testuser1", password="testpass123")

        edit_data = {"content": "Updated content"}

        response = self.client.patch(
            reverse("post", kwargs={"post_id": self.post.id}),
            json.dumps(edit_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Post updated successfully.")
        self.assertEqual(data["post"]["content"], "Updated content")

        updated_post = Post.objects.get(id=self.post.id)
        self.assertEqual(updated_post.content, "Updated content")

    def test_edit_post_unauthenticated(self):
        """Test post edit when user is not logged in"""
        edit_data = {"content": "Updated content"}

        response = self.client.patch(
            reverse("post", kwargs={"post_id": self.post.id}),
            json.dumps(edit_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "You must be logged in to edit posts.")

    def test_edit_post_unauthorized(self):
        """Test post edit by non-owner"""
        self.client.login(username="testuser2", password="testpass123")

        edit_data = {"content": "Updated content"}

        response = self.client.patch(
            reverse("post", kwargs={"post_id": self.post.id}),
            json.dumps(edit_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "You can only edit your own posts.")

    def test_edit_post_blank_content(self):
        """Test post edit with blank content"""
        self.client.login(username="testuser1", password="testpass123")

        edit_data = {"content": "   "}  # Only whitespace

        response = self.client.patch(
            reverse("post", kwargs={"post_id": self.post.id}),
            json.dumps(edit_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Post content cannot be blank.")

    def test_edit_nonexistent_post(self):
        """Test editing a post that doesn't exist"""
        self.client.login(username="testuser1", password="testpass123")

        edit_data = {"content": "Updated content"}

        response = self.client.patch(
            reverse("post", kwargs={"post_id": 99999}),
            json.dumps(edit_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content), {"error": "Post not found."})

    def test_edit_post_invalid_json(self):
        """Test post edit with invalid JSON data"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.patch(
            reverse("post", kwargs={"post_id": self.post.id}),
            "invalid json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Invalid JSON data.")

    def test_edit_post_integrity_error(self):
        """Test handling of IntegrityError during post edit"""
        self.client.login(username="testuser1", password="testpass123")

        with patch("network.models.Post.save") as mock_save:
            mock_save.side_effect = IntegrityError()

            response = self.client.patch(
                reverse("post", kwargs={"post_id": self.post.id}),
                json.dumps({"content": "New content"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(
                data["error"], "Data integrity error, please check your input."
            )

    def test_edit_post_validation_error(self):
        """Test handling of ValidationError during post edit"""
        self.client.login(username="testuser1", password="testpass123")

        with patch("network.models.Post.save") as mock_save:
            mock_save.side_effect = ValidationError("Invalid data")

            response = self.client.patch(
                reverse("post", kwargs={"post_id": self.post.id}),
                json.dumps({"content": "New content"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Validation error: Invalid data")

    def test_edit_post_database_error(self):
        """Test handling of DatabaseError during post edit"""
        self.client.login(username="testuser1", password="testpass123")

        with patch("network.models.Post.save") as mock_save:
            mock_save.side_effect = DatabaseError()

            response = self.client.patch(
                reverse("post", kwargs={"post_id": self.post.id}),
                json.dumps({"content": "New content"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(
                data["error"], "Database operation error, please try again later."
            )

    def test_edit_post_general_exception(self):
        """Test handling of general Exception during post edit"""
        self.client.login(username="testuser1", password="testpass123")

        with patch("network.models.Post.save") as mock_save:
            mock_save.side_effect = Exception("Unexpected error")

            response = self.client.patch(
                reverse("post", kwargs={"post_id": self.post.id}),
                json.dumps({"content": "New content"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Unexpected error")


class PostSoftDeleteViewTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username="testuser1", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", password="testpass123"
        )

        # Create test post
        self.post = Post.objects.create(
            content="Original content", created_by=self.user1
        )

        self.client = Client()

    def test_soft_delete_post_success(self):
        """Test successful soft deletion by the owner"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.delete(
            reverse("post", kwargs={"post_id": self.post.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Post deleted successfully.")

        # Verify post is marked as deleted
        updated_post = Post.objects.get(id=self.post.id)
        self.assertTrue(updated_post.is_deleted)
        self.assertEqual(data["post"], updated_post.serialize())

    def test_soft_delete_post_unauthenticated(self):
        """Test soft deletion when user is not logged in"""
        response = self.client.delete(
            reverse("post", kwargs={"post_id": self.post.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "You must be logged in to delete posts.")

        # Verify post is not deleted
        self.assertFalse(Post.objects.get(id=self.post.id).is_deleted)

    def test_soft_delete_post_unauthorized(self):
        """Test soft deletion by non-owner"""
        self.client.login(username="testuser2", password="testpass123")

        response = self.client.delete(
            reverse("post", kwargs={"post_id": self.post.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "You can only delete your own posts.")

        # Verify post is not deleted
        self.assertFalse(Post.objects.get(id=self.post.id).is_deleted)

    def test_soft_delete_nonexistent_post(self):
        """Test soft deletion of a post that doesn't exist"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.delete(
            reverse("post", kwargs={"post_id": 99999}), content_type="application/json"
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Post not found.")

    def test_soft_delete_database_error(self):
        """Test database error during soft deletion"""
        self.client.login(username="testuser1", password="testpass123")

        with patch("network.models.Post.save") as mock_save:
            mock_save.side_effect = DatabaseError()

            response = self.client.delete(
                reverse("post", kwargs={"post_id": self.post.id}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(
                data["error"], "Database operation error, please try again later."
            )

            # Verify post is not deleted
            self.assertFalse(Post.objects.get(id=self.post.id).is_deleted)

    def test_soft_delete_general_exception(self):
        """Test general exception during soft deletion"""
        self.client.login(username="testuser1", password="testpass123")

        with patch("network.models.Post.save") as mock_save:
            mock_save.side_effect = Exception("Unexpected error")

            response = self.client.delete(
                reverse("post", kwargs={"post_id": self.post.id}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Unexpected error")

            # Verify post is not deleted
            self.assertFalse(Post.objects.get(id=self.post.id).is_deleted)


class PostMethodTests(TestCase):
    """Test case for handling HTTP methods in post-related views"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser1", password="testpass123"
        )
        self.post = Post.objects.create(content="Test content", created_by=self.user)
        self.client = Client()
        self.client.login(username="testuser1", password="testpass123")

    def test_posts_list_invalid_methods(self):
        """Test invalid HTTP methods for posts list endpoint"""
        url = reverse("posts")

        # Test all invalid methods
        invalid_methods = ["PUT", "PATCH", "DELETE"]
        for method in invalid_methods:
            response = getattr(self.client, method.lower())(
                url, content_type="application/json"
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Only accept GET and POST method.")

    def test_post_detail_invalid_methods(self):
        """Test invalid HTTP methods for post detail endpoint"""
        url = reverse("post", kwargs={"post_id": self.post.id})

        # Test all invalid methods
        invalid_methods = ["POST", "PUT"]
        for method in invalid_methods:
            response = getattr(self.client, method.lower())(
                url, content_type="application/json"
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(
                data["error"], "Only accept GET, PATCH and DELETE methods."
            )


class UserDetailViewTests(TestCase):
    def setUp(self):
        # Create test users
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )

        # Create test posts
        self.active_post = Post.objects.create(
            content="Active post", created_by=self.user
        )

        self.deleted_post = Post.objects.create(
            content="Deleted post", created_by=self.user, is_deleted=True
        )

        # Create another user for testing follow functionality
        self.other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )

        # Create follow relationship (other_user follows self.user)
        Following.objects.create(follower=self.other_user, following=self.user)

        self.client = Client()

    def test_get_user_detail_success(self):
        """Test successful retrieval of user details"""
        # Note: Following relationship is already created in setUp()
        # No need to create another one

        response = self.client.get(
            reverse("user_detail", kwargs={"username": self.user.username})
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Verify response format and message
        self.assertEqual(data["message"], "Get user detail successfully.")
        self.assertIn("user", data)
        self.assertIn("posts", data)

        # Verify user data
        user_data = data["user"]
        self.assertEqual(user_data["username"], self.user.username)
        self.assertEqual(user_data["email"], self.user.email)
        self.assertEqual(user_data["following_count"], 0)  # user has 0 followings
        self.assertEqual(
            user_data["follower_count"], 1
        )  # user has 1 follower (other_user)

        # Verify posts data
        posts = data["posts"]
        self.assertEqual(len(posts), 1)  # Only active posts
        self.assertEqual(posts[0]["content"], "Active post")

    def test_get_user_detail_no_posts(self):
        """Test user detail retrieval for user with no posts"""
        # Create new user with no posts
        new_user = User.objects.create_user(
            username="newuser", password="testpass123", email="new@example.com"
        )

        response = self.client.get(
            reverse("user_detail", kwargs={"username": new_user.username})
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsNone(data["posts"])

    def test_get_nonexistent_user(self):
        """Test retrieving non-existent user"""
        response = self.client.get(
            reverse("user_detail", kwargs={"username": "nonexistent"})
        )

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
        newer_post = Post.objects.create(
            content="Newer post",
            created_by=self.user,
            created_at=timezone.now() + timedelta(hours=1),
        )

        response = self.client.get(
            reverse("user_detail", kwargs={"username": self.user.username})
        )

        data = json.loads(response.content)
        posts = data["posts"]

        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0]["content"], "Newer post")
        self.assertEqual(posts[1]["content"], "Active post")


class PostLikeViewTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username="testuser1", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", password="testpass123"
        )

        # Create test post
        self.post = Post.objects.create(
            content="Test post content", created_by=self.user1
        )

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
            self.assertEqual(
                data["error"], "Data integrity error, please check your input."
            )

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
            self.assertEqual(
                data["error"], "Database operation error, please try again later."
            )

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


class FollowViewTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username="testuser1", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", password="testpass123"
        )
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
            self.assertEqual(
                data["error"], "Data integrity error, please check your input."
            )

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
            self.assertEqual(
                data["error"], "Database operation error, please try again later."
            )

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
            self.assertEqual(
                data["error"], "Database operation error, please try again later."
            )

            # Verify following relationship still exists
            self.assertTrue(
                Following.objects.filter(
                    follower=self.user1, following=self.user2
                ).exists()
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
        self.user1 = User.objects.create_user(
            username="testuser1", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", password="testpass123"
        )
        self.user3 = User.objects.create_user(
            username="testuser3", password="testpass123"
        )

        # Create test posts
        self.post1 = Post.objects.create(
            content="Test post 1 by user2", created_by=self.user2
        )
        self.post2 = Post.objects.create(
            content="Test post 2 by user2",
            created_by=self.user2,
            is_deleted=True,  # Deleted post
        )
        self.post3 = Post.objects.create(
            content="Test post by user3", created_by=self.user3
        )

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
        user4 = User.objects.create_user(username="testuser4", password="testpass123")
        self.client.login(username="testuser4", password="testpass123")

        response = self.client.get(reverse("posts_following"))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data["posts"]), 0)

    def test_get_following_posts_ordering(self):
        """Test that following posts are ordered by creation time"""
        self.client.login(username="testuser1", password="testpass123")

        # Create newer post by followed user
        newer_post = Post.objects.create(
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
        mock_chain = (
            mock_select_related.return_value.prefetch_related.return_value.filter.return_value.order_by.return_value
        )
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
        self.assertEqual(
            data["error"], "Database operation error, please try again later."
        )

    @patch("network.models.Following.objects.filter")
    def test_general_exception_handling(self, mock_filter):
        """Test handling of general exceptions"""
        self.client.login(username="testuser1", password="testpass123")
        mock_filter.side_effect = Exception("Unexpected error")

        response = self.client.get(reverse("posts_following"))

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Unexpected error")


class CommentViewTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username="testuser1", password="testpass123"
        )

        # Create test post
        self.post = Post.objects.create(
            content="Test post content", created_by=self.user1
        )

        # Initialize test client
        self.client = Client()

    def test_comment_authentication_required(self):
        """Test that authentication is required for commenting"""
        response = self.client.post(
            reverse("comments", kwargs={"post_id": self.post.id}),
            json.dumps({"content": "Test comment"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(
            data["error"],
            "You must be logged in to create, edit or delete your comment.",
        )

    def test_comment_post_not_found(self):
        """Test commenting on non-existent post"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.post(
            reverse("comments", kwargs={"post_id": 99999}),
            json.dumps({"content": "Test comment"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Post not found.")

    def test_comment_invalid_json(self):
        """Test handling of invalid JSON data"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.post(
            reverse("comments", kwargs={"post_id": self.post.id}),
            "Invalid JSON",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Invalid JSON data.")

    def test_comment_empty_content(self):
        """Test commenting with empty content"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.post(
            reverse("comments", kwargs={"post_id": self.post.id}),
            json.dumps({"content": ""}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Comment content can not be empty.")

    def test_comment_successful_creation(self):
        """Test successful comment creation"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.post(
            reverse("comments", kwargs={"post_id": self.post.id}),
            json.dumps({"content": "Test comment"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Comment created successfully.")

        # Verify comment was created in database
        comment = Comment.objects.filter(post=self.post).first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.content, "Test comment")
        self.assertEqual(comment.created_by, self.user1)

    def test_comment_integrity_error(self):
        """Test handling of IntegrityError during comment creation"""
        self.client.login(username="testuser1", password="testpass123")

        with patch("network.models.Comment.objects.create") as mock_create:
            mock_create.side_effect = IntegrityError()

            response = self.client.post(
                reverse("comments", kwargs={"post_id": self.post.id}),
                json.dumps({"content": "Test comment"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(
                data["error"], "Data integrity error, please check your input."
            )

    def test_comment_validation_error(self):
        """Test handling of ValidationError during comment creation"""
        self.client.login(username="testuser1", password="testpass123")

        with patch("network.models.Comment.objects.create") as mock_create:
            mock_create.side_effect = ValidationError("Invalid data")

            response = self.client.post(
                reverse("comments", kwargs={"post_id": self.post.id}),
                json.dumps({"content": "Test comment"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Validation error: Invalid data")

    def test_comment_database_error(self):
        """Test handling of DatabaseError during comment creation"""
        self.client.login(username="testuser1", password="testpass123")

        with patch("network.models.Comment.objects.create") as mock_create:
            mock_create.side_effect = DatabaseError()

            response = self.client.post(
                reverse("comments", kwargs={"post_id": self.post.id}),
                json.dumps({"content": "Test comment"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(
                data["error"], "Database operation error, please try again later."
            )

    def test_comment_general_exception(self):
        """Test handling of general Exception during comment creation"""
        self.client.login(username="testuser1", password="testpass123")

        with patch("network.models.Comment.objects.create") as mock_create:
            mock_create.side_effect = Exception("Unexpected error")

            response = self.client.post(
                reverse("comments", kwargs={"post_id": self.post.id}),
                json.dumps({"content": "Test comment"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Unexpected error")

    def test_comment_invalid_method(self):
        """Test handling of invalid HTTP methods"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.get(
            reverse("comments", kwargs={"post_id": self.post.id})
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Only accept POST method.")


class CommentDetailViewTests(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(
            username="testuser1", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", password="testpass123"
        )

        # Create test post
        self.post = Post.objects.create(
            created_by=self.user1, content="Test post content"
        )

    def test_edit_comment_success(self):
        """Test successful comment edit"""
        self.client.login(username="testuser1", password="testpass123")
        comment = Comment.objects.create(
            created_by=self.user1, post=self.post, content="Original content"
        )

        response = self.client.patch(
            reverse("comment_detail", kwargs={"comment_id": comment.id}),
            json.dumps({"content": "Updated content"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Comment updated successfully.")
        self.assertEqual(data["comment"]["content"], "Updated content")

    def test_edit_comment_unauthorized(self):
        """Test editing comment by non-author"""
        self.client.login(username="testuser2", password="testpass123")
        comment = Comment.objects.create(
            created_by=self.user1, post=self.post, content="Original content"
        )

        response = self.client.patch(
            reverse("comment_detail", kwargs={"comment_id": comment.id}),
            json.dumps({"content": "Updated content"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "You can only edit your own comments.")

    def test_edit_comment_invalid_json(self):
        """Test editing comment with invalid JSON"""
        self.client.login(username="testuser1", password="testpass123")
        comment = Comment.objects.create(
            created_by=self.user1, post=self.post, content="Original content"
        )

        response = self.client.patch(
            reverse("comment_detail", kwargs={"comment_id": comment.id}),
            "invalid json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Invalid JSON data.")

    def test_edit_comment_not_found(self):
        """Test editing non-existent comment"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.patch(
            reverse("comment_detail", kwargs={"comment_id": 99999}),
            json.dumps({"content": "Updated content"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Comment not found.")

    def test_edit_comment_empty_content(self):
        """Test editing comment with empty content"""
        self.client.login(username="testuser1", password="testpass123")
        comment = Comment.objects.create(
            created_by=self.user1, post=self.post, content="Original content"
        )

        response = self.client.patch(
            reverse("comment_detail", kwargs={"comment_id": comment.id}),
            json.dumps({"content": "   "}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Comment content can not be blank.")

    def test_edit_comment_database_error(self):
        """Test handling DatabaseError during comment edit"""
        self.client.login(username="testuser1", password="testpass123")
        comment = Comment.objects.create(
            created_by=self.user1, post=self.post, content="Original content"
        )

        with patch("network.models.Comment.save") as mock_save:
            mock_save.side_effect = DatabaseError()

            response = self.client.patch(
                reverse("comment_detail", kwargs={"comment_id": comment.id}),
                json.dumps({"content": "Updated content"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(
                data["error"], "Database operation error, please try again later."
            )

    def test_edit_comment_validation_error(self):
        """Test handling ValidationError during comment edit"""
        self.client.login(username="testuser1", password="testpass123")
        comment = Comment.objects.create(
            created_by=self.user1, post=self.post, content="Original content"
        )

        with patch("network.models.Comment.save") as mock_save:
            mock_save.side_effect = ValidationError("Invalid content")

            response = self.client.patch(
                reverse("comment_detail", kwargs={"comment_id": comment.id}),
                json.dumps({"content": "Updated content"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Validation error: Invalid content")

    def test_edit_comment_integrity_error(self):
        """Test handling IntegrityError during comment edit"""
        self.client.login(username="testuser1", password="testpass123")
        comment = Comment.objects.create(
            created_by=self.user1, post=self.post, content="Original content"
        )

        with patch("network.models.Comment.save") as mock_save:
            mock_save.side_effect = IntegrityError()

            response = self.client.patch(
                reverse("comment_detail", kwargs={"comment_id": comment.id}),
                json.dumps({"content": "Updated content"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(
                data["error"], "Data integrity error, please check your input."
            )

    def test_edit_comment_general_exception(self):
        """Test handling general Exception during comment edit"""
        self.client.login(username="testuser1", password="testpass123")
        comment = Comment.objects.create(
            created_by=self.user1, post=self.post, content="Original content"
        )

        with patch("network.models.Comment.save") as mock_save:
            mock_save.side_effect = Exception("Unexpected error")

            response = self.client.patch(
                reverse("comment_detail", kwargs={"comment_id": comment.id}),
                json.dumps({"content": "Updated content"}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Unexpected error")

    def test_edit_comment_invalid_method(self):
        """Test handling invalid HTTP methods for comment edit"""
        self.client.login(username="testuser1", password="testpass123")
        comment = Comment.objects.create(
            created_by=self.user1, post=self.post, content="Original content"
        )

        response = self.client.post(
            reverse("comment_detail", kwargs={"comment_id": comment.id}),
            json.dumps({"content": "Updated content"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Only accept PATCH and DELETE methods.")

    def test_delete_comment_successful(self):
        """Test successful comment deletion"""
        self.client.login(username="testuser1", password="testpass123")
        comment = Comment.objects.create(
            created_by=self.user1, post=self.post, content="Test comment"
        )

        response = self.client.delete(
            reverse("comment_detail", kwargs={"comment_id": comment.id})
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Comment deleted successfully.")

        # Verify comment was soft deleted
        comment.refresh_from_db()
        self.assertTrue(comment.is_deleted)

    def test_delete_comment_unauthorized(self):
        """Test deleting comment by unauthorized user"""
        self.client.login(username="testuser2", password="testpass123")
        comment = Comment.objects.create(
            created_by=self.user1, post=self.post, content="Test comment"
        )

        response = self.client.delete(
            reverse("comment_detail", kwargs={"comment_id": comment.id})
        )

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "You can only delete your own comments.")

    def test_delete_nonexistent_comment(self):
        """Test deleting non-existent comment"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.delete(
            reverse("comment_detail", kwargs={"comment_id": 99999})
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Comment not found.")

    def test_delete_comment_database_error(self):
        """Test handling DatabaseError during comment deletion"""
        self.client.login(username="testuser1", password="testpass123")
        comment = Comment.objects.create(
            created_by=self.user1, post=self.post, content="Test comment"
        )

        with patch("network.models.Comment.save") as mock_save:
            mock_save.side_effect = DatabaseError()

            response = self.client.delete(
                reverse("comment_detail", kwargs={"comment_id": comment.id})
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(
                data["error"], "Database operation error, please try again later."
            )

    def test_delete_comment_general_exception(self):
        """Test handling general Exception during comment deletion"""
        self.client.login(username="testuser1", password="testpass123")
        comment = Comment.objects.create(
            created_by=self.user1, post=self.post, content="Test comment"
        )

        with patch("network.models.Comment.save") as mock_save:
            mock_save.side_effect = Exception("Unexpected error")

            response = self.client.delete(
                reverse("comment_detail", kwargs={"comment_id": comment.id})
            )

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Unexpected error")


    