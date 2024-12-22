import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import MainLayout from "../src/layouts/MainLayout";
import { AuthProvider } from "../src/contexts/AuthContext";
import * as authService from "../src/services/authService";
import React from "react";

// Mock the authService
vi.mock("../src/services/authService", () => ({
  checkAuthStatus: vi.fn(),
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
});
