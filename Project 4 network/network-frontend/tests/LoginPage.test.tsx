import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import LoginPage from "../src/pages/LoginPage";
import * as authService from "../src/services/authService";
import { describe, expect, beforeEach, vi, test } from "vitest";
import React from "react";

// Mock the authService
vi.mock("../src/services/authService");

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock AuthContext
const mockSetUser = vi.fn();
vi.mock("../src/contexts/AuthContext", () => ({
  useAuth: () => ({
    setUser: mockSetUser,
    user: null,
    loading: false,
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

const renderLoginPage = () => {
  return render(
    <BrowserRouter>
      <LoginPage />
    </BrowserRouter>
  );
};

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Test component rendering
  test("renders login form with all necessary elements", () => {
    renderLoginPage();

    expect(screen.getByRole("heading", { name: /login/i })).toBeDefined();
    expect(screen.getByLabelText(/username/i)).toBeDefined();
    expect(screen.getByLabelText(/password/i)).toBeDefined();
    expect(screen.getByRole("button", { name: /login/i })).toBeDefined();
  });

  // Test form validation - empty fields
  test("shows error message when submitting empty form", async () => {
    renderLoginPage();

    const submitButton = screen.getByRole("button", { name: /login/i });
    await userEvent.click(submitButton);

    expect(screen.getByText("Please fill in all fields")).toBeTruthy();
  });

  // Test form validation - empty username
  test("shows error message when submitting form with empty username", async () => {
    renderLoginPage();

    const passwordInput = screen.getByLabelText(/password/i);
    await userEvent.type(passwordInput, "password123");

    const submitButton = screen.getByRole("button", { name: /login/i });
    await userEvent.click(submitButton);

    expect(screen.getByText("Please fill in all fields")).toBeTruthy();
  });

  // Test form validation - empty password
  test("shows error message when submitting form with empty password", async () => {
    renderLoginPage();

    const usernameInput = screen.getByLabelText(/username/i);
    await userEvent.type(usernameInput, "testuser");

    const submitButton = screen.getByRole("button", { name: /login/i });
    await userEvent.click(submitButton);

    expect(screen.getByText("Please fill in all fields")).toBeTruthy();
  });

  // Test successful login
  test("handles successful login and navigation", async () => {
    const mockUser = {
      id: 1,
      username: "testuser",
      email: "test@example.com",
      following_count: 0,
      follower_count: 0,
    };
    vi.mocked(authService.loginUser).mockResolvedValueOnce({
      user: mockUser,
      message: "",
    });

    renderLoginPage();

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);

    await userEvent.type(usernameInput, "testuser");
    await userEvent.type(passwordInput, "password123");

    const submitButton = screen.getByRole("button", { name: /login/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(authService.loginUser).toHaveBeenCalledWith(
        "testuser",
        "password123"
      );
      expect(mockNavigate).toHaveBeenCalledWith("/");
    });
  });

  // Test login failure - invalid credentials
  test("handles login failure with invalid credentials", async () => {
    vi.mocked(authService.loginUser).mockRejectedValueOnce(
      new Error("Invalid credentials")
    );

    renderLoginPage();

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);

    await userEvent.type(usernameInput, "testuser");
    await userEvent.type(passwordInput, "wrongpassword");

    const submitButton = screen.getByRole("button", { name: /login/i });
    await userEvent.click(submitButton);
    await waitFor(() => {
      expect(screen.getByText("Invalid credentials")).toBeTruthy();
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  // Test login failure - server error
  test("handles login failure with server error", async () => {
    vi.mocked(authService.loginUser).mockRejectedValueOnce(
      new Error("Server error")
    );

    renderLoginPage();

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);

    await userEvent.type(usernameInput, "testuser");
    await userEvent.type(passwordInput, "password123");

    const submitButton = screen.getByRole("button", { name: /login/i });
    await userEvent.click(submitButton);
    await waitFor(() => {
      expect(screen.getByText("Server error")).toBeTruthy();
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  // Test input field updates
  test("updates input fields when typing", async () => {
    renderLoginPage();

    const usernameInput = screen.getByLabelText(
      /username/i
    ) as HTMLInputElement;
    const passwordInput = screen.getByLabelText(
      /password/i
    ) as HTMLInputElement;

    await userEvent.type(usernameInput, "testuser");
    await userEvent.type(passwordInput, "password123");

    expect(usernameInput.value).toBe("testuser");
    expect(passwordInput.value).toBe("password123");
  });
});
