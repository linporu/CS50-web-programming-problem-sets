import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LoginPage from "../src/pages/LoginPage";
import { describe, expect, beforeEach, vi } from "vitest";

describe("LoginPage", () => {
  // Reset before each test
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Test component rendering
  test("renders login form with all necessary elements", () => {
    render(<LoginPage />);

    expect(screen.getByRole("heading", { name: /login/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /login/i })).toBeInTheDocument();
  });

  // Test form validation
  test("shows error message when submitting empty form", async () => {
    render(<LoginPage />);

    const submitButton = screen.getByRole("button", { name: /login/i });
    await userEvent.click(submitButton);

    expect(screen.getByText("Please fill in all fields")).toBeInTheDocument();
  });

  // Test form submission
  test("handles form submission with valid inputs", async () => {
    const consoleSpy = vi.spyOn(console, "log");
    render(<LoginPage />);

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);

    await userEvent.type(usernameInput, "testuser");
    await userEvent.type(passwordInput, "password123");

    const submitButton = screen.getByRole("button", { name: /login/i });
    await userEvent.click(submitButton);

    expect(consoleSpy).toHaveBeenCalledWith("Form submitted:", {
      username: "testuser",
      password: "password123",
    });

    consoleSpy.mockRestore();
  });
});
