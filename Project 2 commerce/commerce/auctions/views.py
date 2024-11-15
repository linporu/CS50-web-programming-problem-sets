from decimal import Decimal
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from .models import User, Listing, Bid, Comment, Category, Watchlist
from .utils import *


def index(request):
    listings = Listing.objects.filter(state=Listing.ListingState.ACTIVE)[:10] # Only top 10 active listings
    return render(request, "auctions/index.html", {
        "listings": listings
    })


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
    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        starting_bid = float(request.POST["starting_bid"])
        category = request.POST.get("category", "")  # Optional field
        url = request.POST.get("url", "")  # Optional field
        created_by = request.user

        # Input validation
        errors = []
        if not title:
            errors.append("Title is required")
        if not description:
            errors.append("Description is required")
        if not starting_bid or float(starting_bid) <= 0:
            errors.append("Starting bid must be greater than 0")

        if errors:
            message = Message.error("Please correct the following errors:", errors)
            return render(request, "auctions/create-listing.html", {
                "message": message,
                "listing": {  # Keep input data
                    "title": title,
                    "description": description,
                    "starting_bid": starting_bid,
                    "category": category,
                    "url": url
                }
            })
        
        try:
            listing = Listing(
                title=title,
                description=description,
                starting_bid=starting_bid,
                url=url,
                created_by=created_by
            )
            listing.save()
            message = Message.success("Listing created succussfully")
            return render(request, "auctions/create-listing.html", {
                "message": message
            })
            
        except Exception as e:
            message = Message.error(e)
            return render(request, "auctions/create-listing.html", {
                "message": message
            })
    
    return render(request, "auctions/create-listing.html")


def active_listings(request):
    listings = Listing.objects.filter(state=Listing.ListingState.ACTIVE)
    return render(request, "auctions/active-listings.html", {
        "listings": listings
    })


def listing_page(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    if request.method == "POST":
        if request.user.is_authenticated:
            price = Decimal(request.POST["bid_price"])
            current_price = Decimal(listing.current_price)
            bidder = request.user
            if price < listing.starting_bid:
                message = Message.error(f"Bid price should be greater than starting bid ({listing.starting_bid})")
                return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "message": message,
                    "bid_price": price
                })
            elif price <= current_price:
                message = Message.error(f"Bid should be greater than current price ({listing.current_price})")
                return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "message": message,
                    "bid_price": price
                })
            else:
                try:
                    bid = Bid(
                        listing= listing,
                        price=price,
                        bidder=bidder                     
                    )
                    bid.save()
                    listing.update_price(price)
                    message = Message.success("Bid placed successfully")
                    return render(request, "auctions/listing.html", {
                        "listing": listing,
                        "message": message,
                        "bid_price": price
                    })

                except Exception as e:
                    message = Message.error(e)
                    return render(request, "auctions/listing.html", {
                        "message": message,

                    })
        return render(request, "auctions/login.html")
    return render(request, "auctions/listing.html", {
        "listing": listing
    })


@login_required
def edit_listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    # Check whether the user is the linsting creater
    if request.user != listing.created_by:
        return HttpResponseRedirect(reverse("listing_page", args=[listing_id]))

    # POST request
    if request.method == "POST":
        listing.title = request.POST["title"]
        listing.description = request.POST["description"]
        listing.url = request.POST.get("url", "")
        
        # Error handling
        errors = []
        if not listing.title:
            errors.append("Title is required")
        if not listing.description:
            errors.append("Description is required")
            
        if errors:
            return render(request, "auctions/edit.html", {
                "listing": listing,
                "errors": errors
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
        "listing": listing
    })
    