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

    def test_post_serialize(self):
        """Test the serialize method of Post model"""
        serialized_post = self.post.serialize()
        
        self.assertEqual(serialized_post['id'], self.post.id)
        self.assertEqual(serialized_post['content'], self.post.content)
        self.assertEqual(serialized_post['created_by'], self.post.created_by.username)
        self.assertEqual(serialized_post['created_at'], self.post.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        self.assertEqual(serialized_post['is_deleted'], self.post.is_deleted)

class PostsListViewTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Create test posts
        self.post1 = Post.objects.create(
            content='Test post 1',
            created_by=self.user,
            created_at=timezone.now()
        )
        
        self.post2 = Post.objects.create(
            content='Test post 2',
            created_by=self.user,
            created_at=timezone.now() + timedelta(hours=1)
        )
        
        # Create a soft-deleted post
        self.deleted_post = Post.objects.create(
            content='Deleted post',
            created_by=self.user,
            is_deleted=True
        )
        
        # Create test client
        self.client = Client()

    def test_get_posts_exclude_deleted(self):
        """Ensure soft-deleted posts are not included in the response"""
        response = self.client.get(reverse('posts'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        posts = data['posts']
        
        # Check that the number of posts returned is correct (excluding deleted)
        self.assertEqual(len(posts), 2)
        
        # Ensure the deleted post is not in the response
        post_contents = [post['content'] for post in posts]
        self.assertNotIn('Deleted post', post_contents)

    def test_get_posts_order(self):
        """Ensure posts are returned in reverse chronological order"""
        response = self.client.get(reverse('posts'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        posts = data['posts']
        
        # Check that posts are ordered from newest to oldest
        self.assertEqual(posts[0]['content'], 'Test post 2')
        self.assertEqual(posts[1]['content'], 'Test post 1')

    def test_get_posts_response_format(self):
        """Check the response format and message on successful retrieval"""
        response = self.client.get(reverse('posts'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Verify the structure of the response
        self.assertIn('message', data)
        self.assertIn('posts', data)
        self.assertEqual(data['message'], 'Get posts successfully.')
        
        # Verify the format of each post
        for post in data['posts']:
            self.assertIn('id', post)
            self.assertIn('content', post)
            self.assertIn('created_by', post)
            self.assertIn('created_at', post)

class PostsCreateViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.client = Client()

    def test_create_post_authenticated(self):
        """Test post creation when user is authenticated"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(
            reverse('posts'),
            json.dumps({'content': 'New test post'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Post created successfully.')
        self.assertTrue(Post.objects.filter(content='New test post').exists())

    def test_create_post_unauthenticated(self):
        """Test post creation when user is not authenticated"""
        response = self.client.post(
            reverse('posts'),
            json.dumps({'content': 'New test post'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'You must be logged in to post.')

    def test_invalid_method(self):
        """Ensure error is returned for invalid HTTP methods"""
        response = self.client.put(reverse('posts'))
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Only accept GET and POST method.')

class PostEditViewTests(TestCase):
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
            content='Original content',
            created_by=self.user1
        )
        
        self.client = Client()
        
    def test_edit_post_success(self):
        """Test successful post edit by the owner"""
        self.client.login(username='testuser1', password='testpass123')
        
        # Prepare edit data
        edit_data = {
            'content': 'Updated content'
        }
        
        # Send edit request
        response = self.client.post(
            reverse('post', kwargs={'post_id': self.post.id}),
            json.dumps(edit_data),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Post updated successfully.')
        
        # Verify post was updated in database
        updated_post = Post.objects.get(id=self.post.id)
        self.assertEqual(updated_post.content, 'Updated content')
        
        # Verify updated_at was changed
        self.assertNotEqual(updated_post.updated_at, updated_post.created_at)

    def test_edit_post_unauthenticated(self):
        """Test post edit when user is not logged in"""
        edit_data = {
            'content': 'Updated content'
        }
        
        response = self.client.post(
            reverse('post', kwargs={'post_id': self.post.id}),
            json.dumps(edit_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'You must be logged in to edit posts.')

    def test_edit_post_unauthorized(self):
        """Test post edit by non-owner"""
        # Login as different user
        self.client.login(username='testuser2', password='testpass123')
        
        edit_data = {
            'content': 'Updated content'
        }
        
        response = self.client.post(
            reverse('post', kwargs={'post_id': self.post.id}),
            json.dumps(edit_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'You can only edit your own posts.')

    def test_edit_post_blank_content(self):
        """Test post edit with blank content"""
        self.client.login(username='testuser1', password='testpass123')
        
        edit_data = {
            'content': ''
        }
        
        response = self.client.post(
            reverse('post', kwargs={'post_id': self.post.id}),
            json.dumps(edit_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Post content cannot be blank.')

    def test_edit_nonexistent_post(self):
        """Test editing a post that doesn't exist"""
        self.client.login(username='testuser1', password='testpass123')
        
        edit_data = {
            'content': 'Updated content'
        }
        
        # Use a non-existing post_id
        response = self.client.post(
            reverse('post', kwargs={'post_id': 99999}),
            json.dumps(edit_data),
            content_type='application/json'
        )
      
        self.assertEqual(
            json.loads(response.content),
            {'error': 'Post not found.'}
        )

    def test_edit_post_invalid_json(self):
        """Test post edit with invalid JSON data"""
        self.client.login(username='testuser1', password='testpass123')
        
        # Send invalid JSON
        response = self.client.post(
            reverse('post', kwargs={'post_id': self.post.id}),
            '{invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid JSON data.')

    def test_edit_post_response_format(self):
        """Test the format of successful edit response"""
        self.client.login(username='testuser1', password='testpass123')
        
        edit_data = {
            'content': 'Updated content'
        }
        
        response = self.client.post(
            reverse('post', kwargs={'post_id': self.post.id}),
            json.dumps(edit_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify response structure
        self.assertIn('message', data)
        self.assertIn('post', data)
        
        # Verify post data structure
        post_data = data['post']
        self.assertIn('id', post_data)
        self.assertIn('content', post_data)
        self.assertIn('created_by', post_data)
        self.assertIn('created_at', post_data)
        self.assertIn('updated_at', post_data)
        self.assertIn('is_deleted', post_data)

class PostSoftDeleteViewTests(TestCase):
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
            content='Original content',
            created_by=self.user1
        )
        
        self.client = Client()

    def test_soft_delete_post_success(self):
        """Test successful soft deletion by the owner"""
        self.client.login(username='testuser1', password='testpass123')
        
        response = self.client.put(
            reverse('post', kwargs={'post_id': self.post.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Post deleted successfully.')
        
        # Verify post is marked as deleted
        self.assertTrue(Post.objects.get(id=self.post.id).is_deleted)

    def test_soft_delete_post_unauthenticated(self):
        """Test soft deletion when user is not logged in"""
        response = self.client.put(
            reverse('post', kwargs={'post_id': self.post.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'You must be logged in to delete posts.')

    def test_soft_delete_post_unauthorized(self):
        """Test soft deletion by non-owner"""
        self.client.login(username='testuser2', password='testpass123')
        
        response = self.client.put(
            reverse('post', kwargs={'post_id': self.post.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'You can only delete your own posts.')

    def test_soft_delete_nonexistent_post(self):
        """Test soft deletion of a post that doesn't exist"""
        self.client.login(username='testuser1', password='testpass123')
        
        response = self.client.put(
            reverse('post', kwargs={'post_id': 99999}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Post not found.')

    def test_soft_delete_post_invalid_method(self):
        """Ensure error is returned for invalid HTTP methods"""
        self.client.login(username='testuser1', password='testpass123')
        
        # Test GET method
        response = self.client.get(
            reverse('post', kwargs={'post_id': self.post.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Only accept POST and PUT method.')
        
        # Test DELETE method
        response = self.client.delete(
            reverse('post', kwargs={'post_id': self.post.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Only accept POST and PUT method.')
