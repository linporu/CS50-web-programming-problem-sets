import json
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, DatabaseError, transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from .models import User, Post, Following, Like, Comment


def index(request):
    return render(request, "network/index.html")


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]

        # Validate required fields
        if not username or not email or not password or not confirmation:
            return render(request, "network/register.html", {
                "message": "All fields are required."
            })

        # Ensure password matches confirmation
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


def posts(request):

    # Create new post
    if request.method == "POST":

        # Authenticate before handling POST request
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'You must be logged in to post.'
            }, status=401)
        
        # Check if JSON data valid
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data.'
            }, status=400)

        # Check if content exist    
        if not data.get('content'):
            return JsonResponse({
                'error': 'Post content cannot be empty.'
            }, status=400)
        
        # Create new post in database
        try:
            Post.objects.create(
                content=data.get('content'),
                created_by=request.user
            )
            
            return JsonResponse({
                'message': 'Post created successfully.'
            }, status=200)
        
        except IntegrityError:
            return JsonResponse({
                'error': 'Data integrity error, please check your input.'
            }, status=400)
        except ValidationError as e:
            return JsonResponse({
                'error': f'Validation error: {str(e).strip("[]\'")}'
            }, status=400)
        except DatabaseError:
            return JsonResponse({
                'error': 'Database operation error, please try again later.'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
        
    # Get posts
    elif request.method == "GET":
        try:
            posts = Post.objects.select_related(
                'created_by'
            ).prefetch_related(
                'likes', 
                'comments'
            ).filter(
                is_deleted=False
            ).order_by("-created_at")

            return JsonResponse({
                'message': 'Get posts successfully.',
                'posts': [post.serialize() for post in posts]
            }, status=200)
        
        except Post.DoesNotExist:
            return JsonResponse({
                'error': 'Posts do not exist.'
            }, status=404)
        except DatabaseError:
            return JsonResponse({
                'error': 'Database operation error, please try again later.'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)

    # Not GET or POST
    else:
        return JsonResponse({"error": "Only accept GET and POST method."}, status=400)
    

def post_detail(request, post_id):

    # Get post detail
    if request.method == "GET":
        try:
            post = Post.objects.select_related('created_by').get(pk=post_id)

            if post.is_deleted:
                return JsonResponse({
                    'error': 'This post has been deleted by the author.'
                }, status=410)
            
            return JsonResponse({
                'message': 'Get post successfully.',
                'post': post.serialize()
            }, status=200)

        except Post.DoesNotExist:
            return JsonResponse({
                'error': 'Post not found.'
            }, status=404)
        except DatabaseError:
            return JsonResponse({
                'error': 'Database operation error, please try again later.'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)

    # Edit post
    if request.method == "PATCH":

        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'You must be logged in to edit posts.'
            }, status=401)

        try:
            data = json.loads(request.body)
            post = Post.objects.get(pk=post_id)

            # Check if the logged-in user is the post author
            if post.created_by != request.user:
                return JsonResponse({
                    'error': 'You can only edit your own posts.'
                }, status=403)

            # Validate content
            content = data.get("content", "").strip()
            if not content:
                return JsonResponse({
                    'error': 'Post content cannot be blank.'
                }, status=400)
            
            # Save post content
            with transaction.atomic():
                post.content = content
                post.save()

            return JsonResponse({
                'message': 'Post updated successfully.',
                'post': post.serialize()  # Return updated post
            }, status=200)
        
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data.'
            }, status=400)
        except Post.DoesNotExist:
            return JsonResponse({
                'error': 'Post not found.'
            }, status=404)
        except IntegrityError:
            return JsonResponse({
                'error': 'Data integrity error, please check your input.'
            }, status=400)
        except ValidationError as e:
            return JsonResponse({
                'error': f'Validation error: {str(e).strip("[]\'")}'
            }, status=400)
        except DatabaseError:
            return JsonResponse({
                'error': 'Database operation error, please try again later.'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)

        
    # Soft delete post
    elif request.method == "DELETE":

        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'You must be logged in to delete posts.'
            }, status=401)
        
        try:
            post = Post.objects.get(pk=post_id)
        
            # Check if the logged-in user is the post author
            if post.created_by != request.user:
                return JsonResponse({
                    'error': 'You can only delete your own posts.'
                }, status=403)
            
            # Save post deletion state
            with transaction.atomic():
                post.is_deleted = True
                post.save()

            return JsonResponse({
                'message': 'Post deleted successfully.',
                    'post': post.serialize()  # Return updated post
            }, status=200)
        
        except Post.DoesNotExist:
            return JsonResponse({
                'error': 'Post not found.'
            }, status=404)
        except DatabaseError:
            return JsonResponse({
                'error': 'Database operation error, please try again later.'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    # Not GET, PATCH or DELETE request
    else:
        return JsonResponse({"error": "Only accept GET, PATCH and DELETE methods."}, status=400)


def like(request, post_id):
    
    # Check if user is authenticated for both POST and DELETE
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'You must be logged in to like posts.'
        }, status=401)
    
    # Check if post exists
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return JsonResponse({
            'error': 'Post not found.'
        }, status=404)

    # Like a post
    if request.method == "POST":
        # Check if already liked
        if Like.objects.filter(user=request.user, post=post).exists():
            return JsonResponse({
                'error': 'You have already liked this post.'
            }, status=400)
        
        # Create new like
        try:
            Like.objects.create(user=request.user, post=post)
            return JsonResponse({
                'message': 'Post liked successfully.'
            }, status=200)
        
        except IntegrityError:
            return JsonResponse({
                'error': 'Data integrity error, please check your input.'
            }, status=400)
        except ValidationError as e:
            return JsonResponse({
                'error': f'Validation error: {str(e).strip("[]\'")}'
            }, status=400)
        except DatabaseError:
            return JsonResponse({
                'error': 'Database operation error, please try again later.'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    # Unlike a post
    elif request.method == "DELETE":
        # Check if like exists
        like = Like.objects.filter(user=request.user, post=post)
        if not like.exists():
            return JsonResponse({
                'error': 'You have not liked this post.'
            }, status=400)
        
        # Remove like
        try:
            like.delete()
            return JsonResponse({
                'message': 'Post unliked successfully.'
            }, status=200)
        except DatabaseError:
            return JsonResponse({
                'error': 'Database operation error.'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    # Invalid method
    return JsonResponse({
        'error': 'Only accept POST and DELETE methods.'
    }, status=405)
        

def user_detail(request, username):
    # Get user detail
    if request.method == "GET":
        try:
            user = User.objects.get(username=username)
            
            posts = Post.objects.filter(
                created_by=user,
                is_deleted=False
            ).select_related(
                'created_by'
            ).prefetch_related(
                'likes', 
                'comments'
            ).order_by('-created_at')

            return JsonResponse({
                'message': 'Get user detail successfully.',
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'following_count': user.following_count,
                    'follower_count': user.follower_count,
                },
                'posts': [post.serialize() for post in posts] if posts else None,    
            }, status=200)

        except User.DoesNotExist:
            return JsonResponse({
                'error': 'User not found.'
            }, status=404)
        except DatabaseError:
            return JsonResponse({
                'error': 'Database operation failed.'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': f'Unexpected error: {str(e)}'
            }, status=500)
    
    # Invalid method
    return JsonResponse({
        'error': 'Only accept GET methods.'
    }, status=405)


def follow(request, username):

    user = request.user

    # Check if user is authenticated
    if not user.is_authenticated:
        return JsonResponse({
            'error': 'You must be logged in to view following posts, follow/unfollow users.'
        }, status=401)
    
    # Check if target user exists
    try:
        target_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({
            'error': 'User not found.'
        }, status=404)
    
    # Check if user and target user are the same one
    if user == target_user:
        return JsonResponse({
            'error': 'You can not follow/unfollow yourself.'
        }, status=403)

    # Follow target user
    if request.method == "POST":

        # Check if already following
        if Following.objects.filter(follower=user, following=target_user).exists():
            return JsonResponse({
                'error': 'You are already following this user.'
            }, status=400)

        try:
            with transaction.atomic():
                Following.objects.create(
                    follower=user,
                    following=target_user
                )
            
            return JsonResponse({
                'message': 'Follow user successfully.',
                'data': {
                    'following_count': user.following_count,
                    'target_user_followers': target_user.follower_count
                }
            }, status=200)

        except IntegrityError:
            return JsonResponse({
                'error': 'Data integrity error, please check your input.'
            }, status=400)
        except ValidationError as e:
            return JsonResponse({
                'error': f'Validation error: {str(e).strip("[]\'")}'
            }, status=400)
        except DatabaseError:
            return JsonResponse({
                'error': 'Database operation error, please try again later.'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)

    # Unfollow other user
    elif request.method == "DELETE":
        try:
            with transaction.atomic():
                following = Following.objects.filter(
                    follower=user,
                    following=target_user
                )
                
                if not following.exists():
                    return JsonResponse({
                        'error': 'You are not following this user.'
                    }, status=400)
                    
                following.delete()

            return JsonResponse({
                'message': 'Unfollow user successfully.',
                'data': {
                    'following_count': user.following_count,
                    'target_user_followers': target_user.follower_count
                }
            }, status=200)

        except DatabaseError:
            return JsonResponse({
                'error': 'Database operation error, please try again later.'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)

    # Not POST or DELETE method
    else:
        return JsonResponse({"error": "Only accept POST and DELETE method."}, status=400)
    

def posts_following(request):
    user = request.user

    # Check if user is authenticated
    if not user.is_authenticated:
        return JsonResponse({
            'error': 'You must be logged in to view following posts, follow/unfollow users.'
        }, status=401)

    # Get following posts
    if request.method == "GET":
        try:
            following_users = Following.objects.filter(
                follower=user
            ).values_list('following', flat=True)

            posts = Post.objects.select_related(
                'created_by'
            ).prefetch_related(
                'likes', 
                'comments'
            ).filter(
                created_by__in=following_users,
                is_deleted=False
            ).order_by("-created_at")

            return JsonResponse({
                'message': 'Get following posts successfully.',
                'posts': [post.serialize() for post in posts]
            }, status=200)
        except Following.DoesNotExist:
            return JsonResponse({
                'error': 'Following user does not exist.'
            }, status=404)
        except Post.DoesNotExist:
            return JsonResponse({
                'error': 'Following post does not exist.'
            }, status=404)
        except DatabaseError:
            return JsonResponse({
                'error': 'Database operation error, please try again later.'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
        
    # Not GET method
    else:
        return JsonResponse({"error": "Only accept GET method."}, status=400)
    

def comments(request, post_id):

    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'You must be logged in to create, edit or delete your comment.'
        }, status=401)
    
    # Check if post exists
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return JsonResponse({
            'error': 'Post not found.'
        }, status=404)

    # Comment a post
    if request.method == "POST":

        # Check if JSON data valid
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data.'
            }, status=400)

        # Check if content exist    
        if not data.get('content'):
            return JsonResponse({
                'error': 'Comment content can not be empty.'
            }, status=400)
        
        # Create new comment
        try:
            comment = Comment.objects.create(
                created_by=request.user,
                post=post,
                content=data.get('content')
            )
            
            return JsonResponse({
                'message': 'Comment created successfully.',
                'comment': comment.serialize()
            }, status=201)
        
        except IntegrityError:
            return JsonResponse({
                'error': 'Data integrity error, please check your input.'
            }, status=400)
        except ValidationError as e:
            return JsonResponse({
                'error': f'Validation error: {str(e).strip("[]\'")}'
            }, status=400)
        except DatabaseError:
            return JsonResponse({
                'error': 'Database operation error, please try again later.'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
        
    # Not POST method
    else:
        return JsonResponse({"error": "Only accept POST method."}, status=400)
    

def comment_detail(request, comment_id):
    pass