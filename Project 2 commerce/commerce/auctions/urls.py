from django.urls import include, path
from django.conf import settings
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create-listing", views.create_listing, name="create_listing"),
    path("active-listings", views.active_listings, name="active_listings"),
    path("listing/<int:listing_id>", views.listing_page, name="listing_page"),
    path("listing/<int:listing_id>/edit", views.edit_listing, name="edit_listing")
]

if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]