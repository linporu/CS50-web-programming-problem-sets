import json
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import DatabaseError, IntegrityError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from network.models import Comment, Post

User = get_user_model()


class CommentViewTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username="testuser1", password="testpass123")

        # Create test post
        self.post = Post.objects.create(content="Test post content", created_by=self.user1)

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
            self.assertEqual(data["error"], "Data integrity error, please check your input.")

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
            self.assertEqual(data["error"], "Database operation error, please try again later.")

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

        # Test invalid methods (PUT, PATCH, DELETE)
        invalid_methods = ["PUT", "PATCH", "DELETE"]
        for method in invalid_methods:
            response = getattr(self.client, method.lower())(
                reverse("comments", kwargs={"post_id": self.post.id}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Only accept GET and POST method.")


class CommentDetailViewTests(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(username="testuser1", password="testpass123")
        self.user2 = User.objects.create_user(username="testuser2", password="testpass123")

        # Create test post
        self.post = Post.objects.create(created_by=self.user1, content="Test post content")

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
            self.assertEqual(data["error"], "Database operation error, please try again later.")

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
            self.assertEqual(data["error"], "Data integrity error, please check your input.")

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

        response = self.client.delete(reverse("comment_detail", kwargs={"comment_id": comment.id}))

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

        response = self.client.delete(reverse("comment_detail", kwargs={"comment_id": comment.id}))

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "You can only delete your own comments.")

    def test_delete_nonexistent_comment(self):
        """Test deleting non-existent comment"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.delete(reverse("comment_detail", kwargs={"comment_id": 99999}))

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
            self.assertEqual(data["error"], "Database operation error, please try again later.")

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


class CommentListViewTests(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(username="testuser1", password="testpass123")
        self.user2 = User.objects.create_user(username="testuser2", password="testpass123")

        # Create test post
        self.post = Post.objects.create(created_by=self.user1, content="Test post content")

        # Create test comments
        self.comment1 = Comment.objects.create(
            created_by=self.user1, post=self.post, content="First comment"
        )
        self.comment2 = Comment.objects.create(
            created_by=self.user2, post=self.post, content="Second comment"
        )
        self.deleted_comment = Comment.objects.create(
            created_by=self.user1,
            post=self.post,
            content="Deleted comment",
            is_deleted=True,
        )

        self.client = Client()

    def test_get_comments_success(self):
        """Test successful retrieval of comments"""
        response = self.client.get(reverse("comments", kwargs={"post_id": self.post.id}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Verify response structure
        self.assertEqual(data["message"], "Get comments successfully.")
        self.assertIn("comments", data)

        # Verify only non-deleted comments are returned
        comments = data["comments"]
        self.assertEqual(len(comments), 2)

        # Verify comments are ordered by creation time (newest first)
        self.assertEqual(comments[0]["content"], "Second comment")
        self.assertEqual(comments[1]["content"], "First comment")

    def test_get_comments_unauthenticated(self):
        """Test getting comments when user is not authenticated"""
        response = self.client.get(reverse("comments", kwargs={"post_id": self.post.id}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Get comments successfully.")
        self.assertIn("comments", data)

        # Verify comments are returned
        comments = data["comments"]
        self.assertEqual(len(comments), 2)  # Should get both non-deleted comments

    def test_create_comment_unauthenticated(self):
        """Test creating comment when user is not authenticated"""
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

    def test_get_comments_nonexistent_post(self):
        """Test getting comments for non-existent post"""
        response = self.client.get(reverse("comments", kwargs={"post_id": 99999}))

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Post not found.")

    def test_get_comments_no_comments(self):
        """Test getting comments when post has no comments"""
        # Create new post without comments
        new_post = Post.objects.create(created_by=self.user1, content="Post without comments")

        response = self.client.get(reverse("comments", kwargs={"post_id": new_post.id}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data["comments"]), 0)

    def test_get_comments_database_error(self):
        """Test handling of database errors when getting comments"""
        with patch("network.models.Comment.objects.select_related") as mock_select_related:
            mock_queryset = mock_select_related.return_value
            mock_queryset.filter.side_effect = DatabaseError()

            response = self.client.get(reverse("comments", kwargs={"post_id": self.post.id}))

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Database operation error, please try again later.")

    def test_get_comments_does_not_exist(self):
        """Test handling of DoesNotExist error when getting comments"""
        with patch("network.models.Comment.objects.select_related") as mock_select_related:
            mock_queryset = mock_select_related.return_value
            mock_queryset.filter.side_effect = Comment.DoesNotExist()

            response = self.client.get(reverse("comments", kwargs={"post_id": self.post.id}))

            self.assertEqual(response.status_code, 404)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Comments do not exist.")

    def test_get_comments_general_exception(self):
        """Test handling of general exceptions when getting comments"""
        with patch("network.models.Comment.objects.select_related") as mock_select_related:
            mock_queryset = mock_select_related.return_value
            mock_queryset.filter.side_effect = Exception("Unexpected error")

            response = self.client.get(reverse("comments", kwargs={"post_id": self.post.id}))

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "Unexpected error")

    def test_get_comments_verify_comment_fields(self):
        """Test that each comment in response contains all required fields"""
        response = self.client.get(reverse("comments", kwargs={"post_id": self.post.id}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        comments = data["comments"]

        for comment in comments:
            self.assertIn("id", comment)
            self.assertIn("content", comment)
            self.assertIn("created_by", comment)
            self.assertIn("created_at", comment)
            self.assertIn("is_deleted", comment)

    def test_get_comments_ordering(self):
        """Test that comments are properly ordered by creation time"""
        # Create a new comment with a later timestamp
        Comment.objects.create(
            created_by=self.user1,
            post=self.post,
            content="Later comment",
            created_at=timezone.now() + timedelta(hours=1),
        )

        response = self.client.get(reverse("comments", kwargs={"post_id": self.post.id}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        comments = data["comments"]

        # Verify comments are ordered by creation time (newest first)
        self.assertEqual(comments[0]["content"], "Later comment")
        self.assertEqual(comments[1]["content"], "Second comment")
        self.assertEqual(comments[2]["content"], "First comment")
