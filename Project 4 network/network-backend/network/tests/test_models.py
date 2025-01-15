from datetime import timedelta


from django.contrib.auth import get_user_model

from django.db.utils import IntegrityError
from django.test import TestCase

from django.utils import timezone

from network.models import Comment, Following, Like, Post

User = get_user_model()

class ModelTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username="testuser1", password="testpass123")
        self.user2 = User.objects.create_user(username="testuser2", password="testpass123")

        # Create test post
        self.post = Post.objects.create(content="Test post content", created_by=self.user1)

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
        Like.objects.create(user=self.user2, post=self.post)

        self.assertEqual(self.post.likes_count, 1)

        # Test that duplicate likes raise an error
        with self.assertRaises(IntegrityError):
            Like.objects.create(user=self.user2, post=self.post)

    def test_follow_user(self):
        """Test follow functionality"""
        Following.objects.create(follower=self.user1, following=self.user2)  # user1 follows user2

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
        Comment.objects.create(post=self.post, content="Test comment 3", created_by=self.user2)
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
        self.assertEqual(serialized_post["likes_count"], self.post.likes_count)
        self.assertEqual(serialized_post["comments_count"], self.post.comments_count)
        self.assertEqual(serialized_post["is_liked"], False)

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
        self.post.serialize()  # Store serialized data in cache
        initial_timestamp = self.post._cache_timestamp

        # Verify cache is valid
        self.assertTrue(self.post.is_cache_valid())

        # Simulate cache about to expire (set time to 24 hours later)
        self.post._cache_timestamp = timezone.now() - timedelta(seconds=Post.CACHE_TIMEOUT - 1)
        self.assertTrue(self.post.is_cache_valid())  # Not expired yet

        # Simulate expired cache
        self.post._cache_timestamp = timezone.now() - timedelta(seconds=Post.CACHE_TIMEOUT + 1)
        self.assertFalse(self.post.is_cache_valid())  # Expired
        # Verify cache is regenerated after expiration
        self.post.serialize()  # No need to store unused variable
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
        self.comment1 = Comment.objects.create(
            post=self.post, content="Test comment 1", created_by=self.user2
        )
        self.comment2 = Comment.objects.create(
            post=self.post,
            content="Test comment 2",
            created_by=self.user2,
            is_deleted=True,  # Deleted comment
        )

        # Serialize post
        serialized_data = self.post.serialize()

        # Verify comment-related data
        self.assertEqual(serialized_data["comments_count"], 1)  # Only count non-deleted comments
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
        Comment.objects.create(post=self.post, content="New comment", created_by=self.user2)

        # Use cached serialized data
        cached_data = self.post.serialize()
        self.assertEqual(cached_data["comments_count"], initial_comments_count)

        # Force cache refresh
        fresh_data = self.post.serialize(force_refresh=True)
        self.assertEqual(fresh_data["comments_count"], initial_comments_count + 1)

    def test_post_serialize_with_deleted_comments(self):
        """Test serialization with soft-deleted comments"""
        # Create active comment
        Comment.objects.create(post=self.post, content="Active comment", created_by=self.user2)
        # Create deleted comment
        Comment.objects.create(
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
