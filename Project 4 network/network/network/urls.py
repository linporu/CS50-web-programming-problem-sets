from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),

    # Posts API
    path("api/posts", views.posts, name="posts"),
    path("api/posts/following", views.posts_following, name="posts_following"),
    path("api/posts/<int:post_id>", views.post_detail, name="post"),
    path("api/posts/<int:post_id>/like", views.like, name="like"),
    path("api/posts/<int:post_id>/comments", views.comments, name="comments"),
    
    # Comment API
    path("api/comment/<int:comment_id>", views.comment_detail, name="comment"),

    # Users API
    path("api/users/<str:username>", views.user_detail, name="user_detail"),
    path("api/users/<str:username>/follow", views.follow, name="follow"),
]
