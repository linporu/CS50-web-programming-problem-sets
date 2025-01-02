import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import MainLayout from "./MainLayout";
import { AuthProvider } from "../contexts/AuthContext";
import * as authService from "../services/authService";
import { logoutApi } from "../services/authService";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// Mock the authService
vi.mock("../services/authService", () => ({
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
    vi.clearAllMocks();
    // Default mock implementation for unauthenticated state
    vi.mocked(authService.checkAuthStatus).mockRejectedValue(
      new Error("Not authenticated")
    );
  });

  it("renders navigation with correct styling", async () => {
    renderMainLayout();
    const nav = await waitFor(() => screen.getByRole("navigation"));
    expect(nav).toHaveClass("bg-gray-100 p-4");
  });

  it("renders navigation and content", async () => {
    renderMainLayout();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Network" })).toBeDefined();
      expect(screen.getByText("Test Content")).toBeDefined();
    });
  });

  it("shows login and register links when user is not authenticated", async () => {
    renderMainLayout();
    await waitFor(() => {
      expect(screen.getByRole("link", { name: "Login" })).toBeDefined();
      expect(screen.getByRole("link", { name: "Register" })).toBeDefined();
    });
  });

  it("shows welcome message, home and following links when user is authenticated", async () => {
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
      expect(screen.getByRole("link", { name: "Home" })).toBeDefined();
      expect(screen.getByRole("link", { name: "Following" })).toBeDefined();
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
      expect(logoutButton).toHaveClass("bg-transparent", "hover:text-gray-700");
      await user.click(logoutButton);

      // Now we should see the loading state
      expect(screen.getByText("Logging out...")).toBeDefined();
      expect(logoutButton).toHaveProperty("disabled", true);
      expect(logoutButton).toHaveClass("disabled:opacity-50");

      // Resolve the logout promise
      resolveLogout!(undefined);

      // Verify final state
      await waitFor(() => {
        expect(screen.getByRole("link", { name: "Login" })).toBeDefined();
        expect(screen.getByRole("link", { name: "Register" })).toBeDefined();
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

      // Verify error message appears in the nav
      await waitFor(() => {
        const errorMessage = screen.getByText("Network error");
        expect(errorMessage).toHaveClass("text-red-500");
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
        expect(screen.getByRole("link", { name: "Login" })).toBeDefined();
      });
    });
  });
});
