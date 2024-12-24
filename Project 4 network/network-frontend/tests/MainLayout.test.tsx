import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import MainLayout from "../src/layouts/MainLayout";
import { AuthProvider } from "../src/contexts/AuthContext";
import * as authService from "../src/services/authService";
import React from "react";
import { logoutApi } from "../src/services/authService";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// Mock the authService
vi.mock("../src/services/authService", () => ({
  checkAuthStatus: vi.fn(),
  logoutApi: vi.fn(),
}));

const renderMainLayout = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <MainLayout>
          <div>Test Content</div>
        </MainLayout>
      </AuthProvider>
    </BrowserRouter>
  );
};

describe("MainLayout", () => {
  beforeEach(() => {
    // Reset all mocks before each test
    vi.resetAllMocks();
    // Default mock implementation for unauthenticated state
    const mockCheckAuthStatus = vi.mocked(authService.checkAuthStatus);
    mockCheckAuthStatus.mockRejectedValue(new Error("Not authenticated"));
  });

  it("renders navigation and content", async () => {
    renderMainLayout();
    // Wait for the loading state to resolve
    await waitFor(() => {
      expect(screen.getByText("Network")).toBeDefined();
      expect(screen.getByText("Test Content")).toBeDefined();
    });
  });

  it("shows login and register links when user is not authenticated", async () => {
    renderMainLayout();
    // Wait for the loading state to resolve
    await waitFor(() => {
      expect(screen.getByText("Login")).toBeDefined();
      expect(screen.getByText("Register")).toBeDefined();
    });
  });

  it("shows welcome message and home link when user is authenticated", async () => {
    // Mock successful authentication
    const mockCheckAuthStatus = vi.mocked(authService.checkAuthStatus);
    mockCheckAuthStatus.mockResolvedValue({
      message: "Authenticated",
      user: {
        id: 1,
        username: "testuser",
        email: "test@example.com",
        following_count: 0,
        follower_count: 0,
      },
    });

    renderMainLayout();

    await waitFor(() => {
      expect(screen.getByText(/Welcome, testuser!/)).toBeDefined();
      expect(screen.getByText("Home")).toBeDefined();
    });
  });

  describe("logout functionality", () => {
    beforeEach(() => {
      // Mock successful authentication for all logout tests
      vi.mocked(authService.checkAuthStatus).mockResolvedValue({
        message: "Authenticated",
        user: {
          id: 1,
          username: "testuser",
          email: "test@example.com",
          following_count: 0,
          follower_count: 0,
        },
      });
    });

    it("handles successful logout", async () => {
      const user = userEvent.setup();

      // Create a controlled Promise for logout
      let resolveLogout: (value: unknown) => void;
      const logoutPromise = new Promise((resolve) => {
        resolveLogout = resolve;
      });
      vi.mocked(logoutApi).mockImplementation(() => logoutPromise);

      renderMainLayout();

      // Wait for the authenticated state
      await waitFor(() => {
        expect(screen.getByText(/Welcome, testuser!/)).toBeDefined();
      });

      // Click logout button
      const logoutButton = screen.getByRole("button", { name: /logout/i });
      await user.click(logoutButton);

      // Now we should see the loading state
      expect(screen.getByText("Logging out...")).toBeDefined();
      expect(logoutButton).toHaveProperty("disabled", true);

      // Resolve the logout promise
      resolveLogout!(undefined);

      // Verify final state
      await waitFor(() => {
        expect(screen.getByText("Login")).toBeDefined();
        expect(screen.getByText("Register")).toBeDefined();
      });
    });

    it("displays error message on logout failure", async () => {
      const user = userEvent.setup();
      vi.mocked(logoutApi).mockRejectedValue(new Error("Network error"));

      renderMainLayout();

      // Wait for the authenticated state
      await waitFor(() => {
        expect(screen.getByText(/Welcome, testuser!/)).toBeDefined();
      });

      // Click logout button
      const logoutButton = screen.getByRole("button", { name: /logout/i });
      await user.click(logoutButton);

      // Verify error message
      await waitFor(() => {
        expect(screen.getByText("Network error")).toBeDefined();
      });

      // Verify user is still logged in
      expect(screen.getByText(/Welcome, testuser!/)).toBeDefined();
    });

    it("disables logout button while processing", async () => {
      const user = userEvent.setup();
      // Create a promise that we can resolve manually
      let resolveLogout: (value: unknown) => void;
      const logoutPromise = new Promise((resolve) => {
        resolveLogout = resolve;
      });
      vi.mocked(logoutApi).mockImplementation(() => logoutPromise);

      renderMainLayout();

      // Wait for the authenticated state
      await waitFor(() => {
        expect(screen.getByText(/Welcome, testuser!/)).toBeDefined();
      });

      // Click logout button
      const logoutButton = screen.getByRole("button", { name: /logout/i });
      await user.click(logoutButton);
      // Verify button is disabled during loading
      expect(logoutButton).toBeDisabled();
      expect(screen.getByText("Logging out...")).toBeDefined();

      // Resolve the logout promise
      resolveLogout!(undefined);

      // Verify final state
      await waitFor(() => {
        expect(screen.getByText("Login")).toBeDefined();
      });
    });
  });
});
