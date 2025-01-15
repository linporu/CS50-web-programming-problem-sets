import json
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()

class AuthenticationViewTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )
        self.client = Client()
        self.register_url = reverse("register")

    def test_register_view_post_success(self):
        """Test successful registration attempt"""
        response = self.client.post(
            self.register_url,
            data=json.dumps(
                {
                    "username": "newuser",
                    "email": "new@example.com",
                    "password": "newpass123",
                    "confirmation": "newpass123",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)

        # Verify response format
        self.assertEqual(data["message"], "Registration successful")
        self.assertIn("user", data)

        # Verify user data
        user_data = data["user"]
        self.assertEqual(user_data["username"], "newuser")
        self.assertEqual(user_data["email"], "new@example.com")
        self.assertEqual(user_data["following_count"], 0)
        self.assertEqual(user_data["follower_count"], 0)

        # Verify user is authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_register_view_post_missing_fields(self):
        """Test registration with missing fields"""
        test_cases = [
            {
                "username": "",
                "email": "test@example.com",
                "password": "pass123",
                "confirmation": "pass123",
            },
            {
                "username": "testuser",
                "email": "",
                "password": "pass123",
                "confirmation": "pass123",
            },
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "",
                "confirmation": "pass123",
            },
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "pass123",
                "confirmation": "",
            },
            {},  # Missing all fields
        ]

        for test_case in test_cases:
            response = self.client.post(
                self.register_url,
                data=json.dumps(test_case),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "All fields are required.")
            self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_register_view_password_mismatch(self):
        """Test registration with mismatched passwords"""
        response = self.client.post(
            self.register_url,
            data=json.dumps(
                {
                    "username": "newuser",
                    "email": "new@example.com",
                    "password": "pass123",
                    "confirmation": "different123",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Passwords must match.")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_register_view_duplicate_username(self):
        """Test registration with existing username"""
        response = self.client.post(
            self.register_url,
            data=json.dumps(
                {
                    "username": "testuser",  # Same as setUp user
                    "email": "another@example.com",
                    "password": "pass123",
                    "confirmation": "pass123",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Username already taken.")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_register_view_invalid_json(self):
        """Test registration with invalid JSON data"""
        response = self.client.post(
            self.register_url,
            data="invalid json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Invalid JSON data.")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_register_view_wrong_method(self):
        """Test registration with wrong HTTP method"""
        methods = ["GET", "PUT", "PATCH", "DELETE"]

        for method in methods:
            response = self.client.generic(method, self.register_url)

            self.assertEqual(response.status_code, 405)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "POST request required.")
            self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_csrf_view_returns_token(self):
        """Test that csrf view returns a CSRF token"""
        response = self.client.get(reverse("csrf"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("csrfToken", data)
        self.assertIsInstance(data["csrfToken"], str)
        self.assertTrue(len(data["csrfToken"]) > 0)

    def test_csrf_view_accepts_get_only(self):
        """Test that csrf view only accepts GET requests"""
        # Test POST request
        response = self.client.post(reverse("csrf"))
        self.assertEqual(response.status_code, 405)

        # Test PUT request
        response = self.client.put(reverse("csrf"))
        self.assertEqual(response.status_code, 405)

        # Test DELETE request
        response = self.client.delete(reverse("csrf"))
        self.assertEqual(response.status_code, 405)

    def test_check_auth_view_authenticated(self):
        """Test check_auth view when user is authenticated"""
        # Log in the test user
        self.client.force_login(self.user)

        response = self.client.get(reverse("check_auth"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Verify response structure and content
        self.assertEqual(data["message"], "User is authenticated")
        self.assertIn("user", data)
        user_data = data["user"]
        self.assertEqual(user_data["id"], self.user.id)
        self.assertEqual(user_data["username"], self.user.username)
        self.assertEqual(user_data["email"], self.user.email)
        self.assertEqual(user_data["following_count"], self.user.following_count)
        self.assertEqual(user_data["follower_count"], self.user.follower_count)

    def test_check_auth_view_unauthenticated(self):
        """Test check_auth view when user is not authenticated"""
        response = self.client.get(reverse("check_auth"))
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "User not authenticated")

    def test_check_auth_view_wrong_method(self):
        """Test check_auth view with wrong HTTP methods"""
        methods = ["POST", "PUT", "PATCH", "DELETE"]

        for method in methods:
            response = self.client.generic(method, reverse("check_auth"))
            self.assertEqual(response.status_code, 405)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "GET request required.")
