import { describe, it, expect, vi, beforeEach, Mock } from "vitest";
import {
  loginUser,
  logoutApi,
  registerApi,
  checkAuthStatus,
} from "./authService";
import { fetchWithConfig } from "./api";

// Mock the fetchWithConfig function
vi.mock("./api", () => ({
  fetchWithConfig: vi.fn(),
}));

describe("authService", () => {
  const mockUser = {
    id: 1,
    username: "testuser",
    email: "test@example.com",
    following_count: 0,
    follower_count: 0,
  };

  const mockResponse = {
    message: "Success",
    user: mockUser,
  };

  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks();
  });

  describe("loginUser", () => {
    it("should call fetchWithConfig with correct parameters and return login response", async () => {
      (fetchWithConfig as Mock).mockResolvedValue(mockResponse);

      const result = await loginUser("testuser", "password123");

      expect(fetchWithConfig).toHaveBeenCalledWith("login", {
        method: "POST",
        body: JSON.stringify({ username: "testuser", password: "password123" }),
      });
      expect(result).toEqual(mockResponse);
    });

    it("should throw error when login fails", async () => {
      const errorMessage = "Invalid credentials";
      (fetchWithConfig as Mock).mockRejectedValue(new Error(errorMessage));

      await expect(loginUser("testuser", "wrongpassword")).rejects.toThrow(
        errorMessage
      );
    });
  });

  describe("logoutApi", () => {
    it("should call fetchWithConfig with correct parameters", async () => {
      (fetchWithConfig as Mock).mockResolvedValue({
        message: "Logged out successfully",
      });

      await logoutApi();

      expect(fetchWithConfig).toHaveBeenCalledWith("/logout", {
        method: "POST",
      });
    });

    it("should throw error when logout fails", async () => {
      const errorMessage = "Logout failed";
      (fetchWithConfig as Mock).mockRejectedValue(new Error(errorMessage));

      await expect(logoutApi()).rejects.toThrow(errorMessage);
    });
  });

  describe("registerApi", () => {
    it("should call fetchWithConfig with correct parameters and return register response", async () => {
      (fetchWithConfig as Mock).mockResolvedValue(mockResponse);

      const result = await registerApi(
        "testuser",
        "test@example.com",
        "password123",
        "password123"
      );

      expect(fetchWithConfig).toHaveBeenCalledWith("register", {
        method: "POST",
        body: JSON.stringify({
          username: "testuser",
          email: "test@example.com",
          password: "password123",
          confirmation: "password123",
        }),
      });
      expect(result).toEqual(mockResponse);
    });

    it("should throw error when registration fails", async () => {
      const errorMessage = "Registration failed";
      (fetchWithConfig as Mock).mockRejectedValue(new Error(errorMessage));

      await expect(
        registerApi(
          "testuser",
          "test@example.com",
          "password123",
          "password123"
        )
      ).rejects.toThrow(errorMessage);
    });
  });

  describe("checkAuthStatus", () => {
    it("should call fetchWithConfig with correct parameters and return auth status", async () => {
      (fetchWithConfig as Mock).mockResolvedValue(mockResponse);

      const result = await checkAuthStatus();

      expect(fetchWithConfig).toHaveBeenCalledWith("check_auth", {
        method: "GET",
      });
      expect(result).toEqual(mockResponse);
    });

    it("should throw error when auth check fails", async () => {
      const errorMessage = "Auth check failed";
      (fetchWithConfig as Mock).mockRejectedValue(new Error(errorMessage));

      await expect(checkAuthStatus()).rejects.toThrow(errorMessage);
    });
  });
});
