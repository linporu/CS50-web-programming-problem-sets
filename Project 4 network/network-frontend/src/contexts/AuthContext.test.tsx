import { describe, it, expect, vi, beforeEach, Mock } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "./AuthContext";
import { checkAuthStatus } from "../services/authService";

// Mock the authService
vi.mock("../services/authService", () => ({
  checkAuthStatus: vi.fn(),
}));

describe("AuthContext", () => {
  beforeEach(() => {
    // Reset mock before each test
    vi.resetAllMocks();
    // Default mock implementation
    (checkAuthStatus as Mock).mockResolvedValue({ user: null });
  });

  it("provides initial auth state and functions", async () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>,
    });

    await act(async () => {
      // Wait for auth check to complete
    });

    expect(result.current.user).toBe(null);
    expect(result.current.isAuthenticated).toBe(false);
    expect(typeof result.current.setUser).toBe("function");
    expect(typeof result.current.clearAuth).toBe("function");
  });

  it("updates auth state when setUser is called", async () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>,
    });

    await act(async () => {
      // Wait for auth check to complete
    });

    const testUser = {
      id: 1,
      username: "testuser",
      email: "test@example.com",
      following_count: 0,
      follower_count: 0,
    };

    act(() => {
      result.current.setUser(testUser);
    });

    expect(result.current.user).toEqual(testUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it("clears auth state when clearAuth is called", async () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>,
    });

    // Wait for initial auth check to complete
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    // Set initial authenticated state
    act(() => {
      result.current.setUser({
        id: 1,
        username: "testuser",
        email: "test@example.com",
        following_count: 0,
        follower_count: 0,
      });
    });

    // Verify user is set
    expect(result.current.user).not.toBe(null);
    expect(result.current.isAuthenticated).toBe(true);

    act(() => {
      result.current.clearAuth();
    });

    expect(result.current.user).toBe(null);
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("verifies auth status on mount", async () => {
    const mockUser = {
      id: 1,
      username: "testuser",
      email: "test@example.com",
      following_count: 0,
      follower_count: 0,
    };

    (checkAuthStatus as Mock).mockResolvedValueOnce({ user: mockUser });

    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>,
    });

    await act(async () => {
      // Wait for auth check to complete
    });

    expect(checkAuthStatus).toHaveBeenCalledTimes(1);
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it("handles auth verification failure", async () => {
    (checkAuthStatus as Mock).mockRejectedValueOnce(new Error("Auth failed"));

    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>,
    });

    await act(async () => {
      // Wait for auth check to complete
    });

    expect(checkAuthStatus).toHaveBeenCalledTimes(1);
    expect(result.current.user).toBe(null);
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("throws error when useAuth is used outside of AuthProvider", () => {
    const consoleError = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});

    expect(() => {
      renderHook(() => useAuth());
    }).toThrow("useAuth must be used within an AuthProvider");

    consoleError.mockRestore();
  });
});
