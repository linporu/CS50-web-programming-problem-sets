import json
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, DatabaseError, transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.core.exceptions import ValidationError
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

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
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
        
        try:
            data = json.loads(request.body)
            
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
                    'error': f'Validation error: {str(e)}'
                }, status=400)
            except DatabaseError:
                return JsonResponse({
                    'error': 'Database operation error, please try again later.'
                }, status=500)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data.'
            }, status=400)
    
    # Get posts
    elif request.method == "GET":
        try:
            posts = Post.objects.select_related('created_by').filter(is_deleted=False)
            # Return posts in reverse chronologial order
            posts = posts.order_by("-created_at").all()
            return JsonResponse({
                'message': 'Get posts successfully.',
                'posts': [post.serialize() for post in posts]
            }, status=200)
        
        except IntegrityError:
            return JsonResponse({
                'error': 'Data integrity error, please check your input.'
            }, status=400)
        except ValidationError as e:
            return JsonResponse({
                'error': f'Validation error: {str(e)}'
            }, status=400)
        except DatabaseError:
            return JsonResponse({
                'error': 'Database operation error, please try again later.'
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
            
            try:
                post = Post.objects.get(pk=post_id)
            except Post.DoesNotExist:
                return JsonResponse({
                    'error': 'Post not found.'
                }, status=404)

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
        except DatabaseError:
            return JsonResponse({
                'error': 'Database operation failed.'
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
        except Post.DoesNotExist:
            return JsonResponse({
                'error': 'Post not found.'
            }, status=404)

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
    
    # Not GET, PATCH or DELETE request
    else:
        return JsonResponse({"error": "Only accept GET, PATCH and DELETE request methods."}, status=400)




def like(request):
    pass


def following(request):
    pass