from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),

    # Posts API
    path("api/posts", views.posts, name="posts"),
    path("api/posts/<int:post_id>", views.post_detail, name="post"),
    path("api/posts/<int:post_id>/like", views.like, name="like"),

    # Users API
    path("api/users/<str:username>", views.user_detail, name="user_detail"),
    path("api/users/<str:username>/following", views.user_following, name="user_following"),
]
