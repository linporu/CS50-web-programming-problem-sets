import json
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import DatabaseError, IntegrityError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from network.models import Like, Post

User = get_user_model()


class PostsListViewTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(username="testuser", password="testpassword")

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
        mock_queryset = mock_select_related.return_value.prefetch_related.return_value
        mock_chain = mock_queryset.filter.return_value.order_by.return_value
        mock_chain.__iter__.side_effect = Post.DoesNotExist("Posts do not exist")

        response = self.client.get(reverse("posts"))

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Posts do not exist.")

    @patch("network.models.Post.objects.select_related")
    def test_get_posts_database_error(self, mock_select_related):
        """Test handling of DatabaseError when getting posts"""
        # Mock the chain of queryset methods
        mock_queryset = mock_select_related.return_value.prefetch_related.return_value
        mock_chain = mock_queryset.filter.return_value.order_by.return_value
        mock_chain.__iter__.side_effect = DatabaseError("Database error")

        response = self.client.get(reverse("posts"))

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Database operation error, please try again later.")

    @patch("network.models.Post.objects.select_related")
    def test_get_posts_general_exception(self, mock_select_related):
        """Test handling of general Exception when getting posts"""
        # Mock the chain of queryset methods
        mock_queryset = mock_select_related.return_value.prefetch_related.return_value
        mock_chain = mock_queryset.filter.return_value.order_by.return_value
        mock_chain.__iter__.side_effect = Exception("Unexpected error")

        response = self.client.get(reverse("posts"))

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Unexpected error")


class PostsCreateViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
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
        self.assertEqual(data["error"], "Data integrity error, please check your input.")

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
        self.assertEqual(data["error"], "Database operation error, please try again later.")

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
        # Create test users
        self.user1 = User.objects.create_user(username="testuser1", password="testpass123")
        self.user2 = User.objects.create_user(username="testuser2", password="testpass123")

        # Create test post
        self.post = Post.objects.create(content="Test post content", created_by=self.user1)

        # Create test like
        self.like = Like.objects.create(user=self.user2, post=self.post)

        self.client = Client()

    def test_get_post_detail_success_authenticated(self):
        """Test successful retrieval of post details when user is authenticated"""
        # Login as user2 (who liked the post)
        self.client.login(username="testuser2", password="testpass123")

        response = self.client.get(reverse("post", kwargs={"post_id": self.post.id}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Get post successfully.")

        post_data = data["post"]
        self.assertEqual(post_data["content"], "Test post content")
        self.assertEqual(post_data["created_by"], "testuser1")
        self.assertTrue(post_data["is_liked"])  # Should be True as user2 liked the post

    def test_get_post_detail_success_unauthenticated(self):
        """Test successful retrieval of post details when user is not authenticated"""
        response = self.client.get(reverse("post", kwargs={"post_id": self.post.id}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Get post successfully.")

        post_data = data["post"]
        self.assertEqual(post_data["content"], "Test post content")
        self.assertEqual(post_data["created_by"], "testuser1")
        self.assertFalse(post_data["is_liked"])  # Should be False for unauthenticated user

    def test_get_post_detail_not_liked(self):
        """Test post detail when authenticated user hasn't liked the post"""
        # Login as user1 (who hasn't liked the post)
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.get(reverse("post", kwargs={"post_id": self.post.id}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        post_data = data["post"]
        self.assertFalse(post_data["is_liked"])  # Should be False as user1 hasn't liked the post

    def test_get_post_detail_success(self):
        """Test successful retrieval of post details"""
        response = self.client.get(reverse("post", kwargs={"post_id": self.post.id}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Get post successfully.")
        self.assertEqual(data["post"]["content"], "Test post content")
        self.assertEqual(data["post"]["created_by"], "testuser1")

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
            mock_queryset = mock_select_related.return_value.prefetch_related.return_value
            mock_queryset.get.side_effect = DatabaseError()

            response = self.client.get(reverse("post", kwargs={"post_id": self.post.id}))

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Database operation error, please try again later.")

    def test_general_exception_handling(self):
        """Test handling of general exceptions"""
        with patch("network.models.Post.objects.select_related") as mock_select_related:
            # Simulate general exception
            mock_queryset = mock_select_related.return_value.prefetch_related.return_value
            mock_queryset.get.side_effect = Exception("Unexpected error")

            response = self.client.get(reverse("post", kwargs={"post_id": self.post.id}))

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Unexpected error")


class PostEditViewTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username="testuser1", password="testpass123")
        self.user2 = User.objects.create_user(username="testuser2", password="testpass123")

        # Create test post
        self.post = Post.objects.create(content="Original content", created_by=self.user1)

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
            self.assertEqual(data["error"], "Data integrity error, please check your input.")

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
            self.assertEqual(data["error"], "Database operation error, please try again later.")

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
        self.user1 = User.objects.create_user(username="testuser1", password="testpass123")
        self.user2 = User.objects.create_user(username="testuser2", password="testpass123")

        # Create test post
        self.post = Post.objects.create(content="Original content", created_by=self.user1)

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
            self.assertEqual(data["error"], "Database operation error, please try again later.")

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
        self.user = User.objects.create_user(username="testuser1", password="testpass123")
        self.post = Post.objects.create(content="Test content", created_by=self.user)
        self.client = Client()
        self.client.login(username="testuser1", password="testpass123")

    def test_posts_list_invalid_methods(self):
        """Test invalid HTTP methods for posts list endpoint"""
        url = reverse("posts")

        # Test all invalid methods
        invalid_methods = ["PUT", "PATCH", "DELETE"]
        for method in invalid_methods:
            response = getattr(self.client, method.lower())(url, content_type="application/json")

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Only accept GET and POST method.")

    def test_post_detail_invalid_methods(self):
        """Test invalid HTTP methods for post detail endpoint"""
        url = reverse("post", kwargs={"post_id": self.post.id})

        # Test all invalid methods
        invalid_methods = ["POST", "PUT"]
        for method in invalid_methods:
            response = getattr(self.client, method.lower())(url, content_type="application/json")

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Only accept GET, PATCH and DELETE methods.")
