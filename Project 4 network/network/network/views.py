import json
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, DatabaseError
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
            
            if not data:
                return JsonResponse({
                    'error': 'Post content cannot be empty.'
                }, status=400)
            
            # Create new post in database
            try:
                Post.objects.create(
                    content=data,
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
    else:
        return render(request, "network/index.html")