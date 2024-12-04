from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Post, Comment, Like, Following
from django.db.utils import IntegrityError
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.test import Client
import json

User = get_user_model()

class ModelTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        
        # Create test post
        self.post = Post.objects.create(
            content='Test post content',
            created_by=self.user1
        )

    def test_create_post(self):
        """Test post creation"""
        self.assertEqual(self.post.content, 'Test post content')
        self.assertEqual(self.post.created_by, self.user1)
        self.assertFalse(self.post.is_deleted)
        self.assertEqual(self.post.likes_count, 0)
        self.assertEqual(self.post.comments_count, 0)

    def test_create_comment(self):
        """Test comment creation"""
        comment = Comment.objects.create(
            post=self.post,
            content='Test comment',
            created_by=self.user2
        )
        
        self.assertEqual(comment.content, 'Test comment')
        self.assertEqual(comment.created_by, self.user2)
        self.assertEqual(self.post.comments_count, 1)
        self.assertFalse(comment.is_deleted)

    def test_like_post(self):
        """Test post like functionality"""
        like = Like.objects.create(
            user=self.user2,
            post=self.post
        )
        
        self.assertEqual(self.post.likes_count, 1)
        
        # Test that duplicate likes raise an error
        with self.assertRaises(IntegrityError):
            Like.objects.create(
                user=self.user2,
                post=self.post
            )

    def test_follow_user(self):
        """Test follow functionality"""
        following = Following.objects.create(
            user=self.user1,
            follower=self.user2
        )
        
        # Verify follow relationship is created
        self.assertTrue(
            Following.objects.filter(
                user=self.user1,
                follower=self.user2
            ).exists()
        )
        
        # Test that duplicate follows raise an error
        with self.assertRaises(IntegrityError):
            Following.objects.create(
                user=self.user1,
                follower=self.user2
            )

    def test_soft_delete_post(self):
        """Test post soft deletion"""
        self.post.is_deleted = True
        self.post.save()
        
        # Verify post is marked as deleted
        self.assertTrue(Post.objects.get(id=self.post.id).is_deleted)

    def test_soft_delete_comment(self):
        """Test comment soft deletion"""
        comment = Comment.objects.create(
            post=self.post,
            content='Test comment',
            created_by=self.user2
        )
        
        comment.is_deleted = True
        comment.save()
        
        # Verify comment is marked as deleted and not counted
        self.assertTrue(Comment.objects.get(id=comment.id).is_deleted)
        self.assertEqual(self.post.comments_count, 0)

    def test_post_ordering(self):
        """Test post ordering"""
        post2 = Post.objects.create(
            content='Test post 2',
            created_by=self.user1
        )
        
        posts = Post.objects.all()
        self.assertEqual(posts[0], post2)  # Newer post should be first
        self.assertEqual(posts[1], self.post)

    def test_comment_ordering(self):
        """Test comment ordering"""
        comment1 = Comment.objects.create(
            post=self.post,
            content='First comment',
            created_by=self.user2
        )
        
        comment2 = Comment.objects.create(
            post=self.post,
            content='Second comment',
            created_by=self.user2
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
        user3 = User.objects.create_user(username='testuser3', password='testpass123')
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
            post=self.post,
            content='Test comment 1',
            created_by=self.user2
        )
        self.assertEqual(self.post.comments_count, 1)
        
        # Add another comment
        comment2 = Comment.objects.create(
            post=self.post,
            content='Test comment 2',
            created_by=self.user2
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
            post=self.post,
            content='Test comment 3',
            created_by=self.user2
        )
        self.assertEqual(self.post.comments_count, 1)

class PostCreationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_create_post_success(self):
        """Test successful post creation"""
        response = self.client.post(reverse('posts'), json.dumps({'content': 'New post content'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Post created successfully.')
        self.assertTrue(Post.objects.filter(content='New post content', created_by=self.user).exists())

    def test_create_post_unauthenticated(self):
        """Test post creation without authentication"""
        self.client.logout()
        response = self.client.post(reverse('posts'), json.dumps({'content': 'New post content'}), content_type='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'You must be logged in to post.')

    def test_create_post_empty_content(self):
        """Test post creation with empty content"""
        response = self.client.post(reverse('posts'), json.dumps({'content': ''}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Post content cannot be empty.')

    def test_create_post_invalid_json(self):
        """Test post creation with invalid JSON"""
        response = self.client.post(reverse('posts'), 'Invalid JSON', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Invalid JSON data.')
