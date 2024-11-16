from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from decimal import Decimal
from django.http import HttpRequest
from .models import Bid, Watchlist, Comment, Listing, Category
from .forms import CommentForm


@dataclass
class Message:
    text: str
    type: str = "success"
    details: Optional[List[str]] = None

    @classmethod
    def success(cls, text: str) -> "Message":
        return cls(text=text, type="success")

    @classmethod
    def error(cls, text: str, details: Optional[List[str]] = None) -> "Message":
        return cls(text=text, type="danger", details=details)

    @classmethod
    def warning(cls, text: str) -> "Message":
        return cls(text=text, type="warning")

    @property
    def bootstrap_class(self) -> str:
        return f"alert-{self.type}"


def handle_bid(request: HttpRequest, listing: Listing, context: Dict[str, Any]) -> None:
    """Handle bid action for a listing
    
    Args:
        request: The HTTP request object
        listing: The Listing object
        context: The template context dictionary
    """
    price = Decimal(request.POST["bid_price"])
    current_price = Decimal(listing.current_price)
    
    if price < listing.starting_bid:
        context["message"] = Message.error(
            f"Bid price should be greater than starting bid ({listing.starting_bid})"
        )
    elif price <= current_price:
        context["message"] = Message.error(
            f"Bid should be greater than current price ({listing.current_price})"
        )
    else:
        try:
            Bid.objects.create(
                listing=listing,
                price=price,
                bidder=request.user
            )
            listing.update_price(price)
            context["message"] = Message.success("Bid placed successfully")
        except Exception as e:
            context["message"] = Message.error(str(e))
    
    context["bid_price"] = price


def handle_watchlist(request: HttpRequest, listing: Listing, context: Dict[str, Any]) -> None:
    """Handle watchlist action for a listing
    
    Args:
        request: The HTTP request object
        listing: The Listing object
        context: The template context dictionary
    """
    try:
        watchlist_item, created = Watchlist.objects.get_or_create(
            user=request.user,
            listing=listing
        )
        if created:
            context["message"] = Message.success("Added to watchlist")
        else:
            watchlist_item.delete()
            context["message"] = Message.success("Removed from watchlist")
        
        context["is_in_watchlist"] = Watchlist.objects.filter(
            user=request.user,
            listing=listing
        ).exists()
    except Exception as e:
        context["message"] = Message.error(str(e))


def handle_close_auction(listing: Listing, context: Dict[str, Any]) -> None:
    """Handle auction closing action
    
    Args:
        listing: The Listing object
        context: The template context dictionary
    """
    try:
        highest_bid = Bid.objects.filter(listing=listing).order_by('-price').first() 
        
        if highest_bid:
            listing.winning_bidder = highest_bid.bidder
            listing.save()
            context["winning_bidder"] = listing.winning_bidder
            context["message"] = Message.success("Auction closed successfully")
        else:
            context["message"] = Message.error("No winning bidder")
        
        listing.state = listing.ListingState.CLOSED
    except Exception as e:
        context["message"] = Message.error(str(e))


def handle_comment(request: HttpRequest, listing: Listing, context: Dict[str, Any]) -> None:
    """Handle comment action for a listing
    
    Args:
        request: The HTTP request object
        listing: The Listing object
        context: The template context dictionary
    """
    comment_form = CommentForm(request.POST)
    if comment_form.is_valid():
        try:
            Comment.objects.create(
                listing=listing,
                content=comment_form.cleaned_data['content'],
                commenter=request.user
            )
            context["message"] = Message.success("Comment added successfully")
            context["comment_form"] = CommentForm()
        except Exception as e:
            context["message"] = Message.error("Failed to add comment. Please try again.")
    else:
        context["message"] = Message.error("Please check your input.")


def validate_listing_input(listing: dict, context: dict) -> bool:
    """Validate input data for creating a listing
    
    Args:
        listing: Dictionary containing listing data from form
        context: Context dictionary to update
    
    Returns:
        bool: Whether validation passed
    """
    errors = []
    
    # Basic field validation
    if not listing["title"]:
        errors.append("Title is required")
    if not listing["description"]:
        errors.append("Description is required")
    
    # Starting bid validation
    try:
        starting_bid = float(listing["starting_bid"])
        if starting_bid <= 0:
            errors.append("Starting bid must be greater than 0")
    except (ValueError, TypeError):
        errors.append("Invalid starting bid value")
    
    # If there are errors, update context and preserve listing data
    if errors:
        context.update({
            "message": Message.error("Please correct the following errors:", errors),
            "listing": {
                "title": listing["title"],
                "description": listing["description"],
                "starting_bid": listing.get("starting_bid", ""),
                "url": listing["url"],
                "categories": Category.objects.filter(
                    id__in=listing["category_ids"]
                ) if listing["category_ids"] else None
            }
        })
        return False
    
    return True


def handle_listing_creation(listing: dict, context: dict) -> tuple[bool, int]:
    """Handle listing creation logic
    
    Args:
        listing: Dictionary containing listing data from form
        context: Context dictionary to update
    
    Returns:
        tuple[bool, int]: (success status, created listing ID)
    """
    try:
        # Create listing
        created_listing = Listing.objects.create(
            title=listing["title"],
            description=listing["description"],
            starting_bid=Decimal(listing["starting_bid"]),
            url=listing["url"],
            created_by=listing["created_by"]
        )
        
        # Handle categories
        if listing["category_ids"]:
            selected_categories = Category.objects.filter(
                id__in=listing["category_ids"]
            )
            created_listing.categories.set(selected_categories)
        else:
            context["message"] = Message.warning("Categories do not exist")
            return False, None

        return True, created_listing.id
        
    except Exception as e:
        context["message"] = Message.error(str(e))
        return False, None

