from decimal import Decimal
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .forms import CommentForm
from .models import User, Listing, Bid, Comment, Category, Watchlist
from .utils import Message, handle_bid, handle_watchlist, handle_close_auction, handle_comment, handle_listing_creation, validate_listing_input


def index(request):
    context = {
        "listings": listings
    }
    listings = Listing.objects.filter(state=Listing.ListingState.ACTIVE)[:10] # Only top 10 active listings
    return render(request, "auctions/index.html", context)


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
            message = Message.error("Invalid username and/or password.")
            return render(request, "auctions/login.html", {
                "message": message
            })
    else:
        return render(request, "auctions/login.html")


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
            message = Message.error("Passwords must match.")
            return render(request, "auctions/register.html", {
                "message": message
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            message = Message.error("Username already taken.")
            return render(request, "auctions/register.html", {
                "message": message
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create_listing(request):
    # Initialize basic context
    context = {
        "all_categories": Category.objects.all()
    }

    # Return directly for GET request
    if request.method == "GET":
        return render(request, "auctions/create-listing.html", context)

    # Collect POST data
    listing_data = {
        "title": request.POST["title"],
        "description": request.POST["description"],
        "starting_bid": request.POST["starting_bid"],
        "category_ids": request.POST.getlist("categories"),
        "url": request.POST.get("url", ""),
        "created_by": request.user
    }

    # Validate input
    if not validate_listing_input(listing_data, context):
        return render(request, "auctions/create-listing.html", context)

    # Handle creation logic
    success, listing_id = handle_listing_creation(listing_data, context)
    if success:
        return redirect('listing_page', listing_id=listing_id)
    
    return render(request, "auctions/create-listing.html", context)


def active_listings(request):
    listings = Listing.objects.filter(state=Listing.ListingState.ACTIVE)
    return render(request, "auctions/active-listings.html", {
        "listings": listings
    })


def listing_page(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    
    # Initialize basic context
    context = {
        "listing": listing,
        "categories": listing.categories.all(),
        "is_in_watchlist": Watchlist.objects.filter(
            user=request.user,
            listing=listing
        ).exists() if request.user.is_authenticated else False,
        "comments": Comment.objects.filter(listing=listing),
        "comment_form": CommentForm(),
        "winning_bidder": listing.winning_bidder if listing.winning_bidder else None
    }

    # Handle GET request
    if request.method == "GET":
        return render(request, "auctions/listing.html", context)

    # Authenticate before handling POST request
    if not request.user.is_authenticated:
        return render(request, "auctions/login.html")

    # Handle POST request
    action = request.POST.get("action")
    
    # Handle different actions
    if action == "bid":
        handle_bid(request, listing, context)
    elif action == "watchlist":
        handle_watchlist(request, listing, context)
    elif action == "close_auction":
        handle_close_auction(listing, context)
    elif action == "comment":
        handle_comment(request, listing, context)

    return render(request, "auctions/listing.html", context)


@login_required
def edit_listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    categories = Category.objects.all()

    # Check whether the user is the linsting creater
    if request.user != listing.created_by:
        return HttpResponseRedirect(reverse("listing_page", args=[listing_id]))

    # POST request
    if request.method == "POST":
        listing.title = request.POST["title"]
        listing.description = request.POST["description"]
        category_ids = request.POST.getlist("categories")
        if category_ids:
            categories = Category.objects.filter(id__in=category_ids)
            listing.categories.set(categories)
        listing.url = request.POST.get("url", "")

        # Error handling
        errors = []
        if not listing.title:
            errors.append("Title is required")
        if not listing.description:
            errors.append("Description is required")
            
        if errors:
            message = Message.error("Error", errors)
            return render(request, "auctions/edit.html", {
                "listing": listing,
                "message": message
            })
            
        try:
            listing.save()
            return HttpResponseRedirect(reverse("listing_page", args=[listing_id]))
        except Exception as e:
            message = Message.error(e)
            return render(request, "auctions/edit.html", {
                "listing": listing,
                "message": message
            })
        
    # GET request
    return render(request, "auctions/edit-listing.html", {
        "listing": listing,
        "categories": categories
    })
    

def categories(request):
    categories = Category.objects.annotate(
        active_count=Count('listings', 
            filter=Q(listings__state=Listing.ListingState.ACTIVE)
        )
    )
    return render(request, "auctions/categories.html", {
        "categories": categories
    })


def category(request, category_id):
    category = Category.objects.get(pk=category_id)
    active_listings = Listing.objects.filter(
        categories=category,
        state=Listing.ListingState.ACTIVE
    )
    
    return render(request, "auctions/category.html", {
        "category": category,
        "listings": active_listings
    })


@login_required
def watchlist(request):
    watched_listings = Listing.objects.filter(watching_users__user=request.user)
    return render(request, "auctions/watchlist.html",{
        "listings": watched_listings
    })