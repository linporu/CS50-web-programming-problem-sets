import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  getUserDetailApi,
  getUserProfileApi,
  getUserPostsApi,
} from "./userService";
import * as api from "./api";

// Mock the fetchWithConfig function
vi.mock("./api", () => ({
  fetchWithConfig: vi.fn(),
}));

describe("userService", () => {
  const mockUsername = "testuser";
  const mockUserResponse = {
    message: "Success",
    user: {
      username: "testuser",
      email: "test@example.com",
      following_count: 10,
      follower_count: 20,
    },
    posts: [
      {
        id: 1,
        content: "Test post",
        author: "testuser",
        timestamp: "2024-01-01T00:00:00Z",
        likes_count: 5,
        liked_by_user: false,
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getUserDetailApi", () => {
    it("should fetch user details successfully", async () => {
      // Arrange
      vi.mocked(api.fetchWithConfig).mockResolvedValueOnce(mockUserResponse);

      // Act
      const result = await getUserDetailApi(mockUsername);

      // Assert
      expect(api.fetchWithConfig).toHaveBeenCalledWith(
        `/api/users/${mockUsername}`,
        { method: "GET" }
      );
      expect(result).toEqual(mockUserResponse);
    });

    it("should handle API error", async () => {
      // Arrange
      const errorMessage = "API Error";
      vi.mocked(api.fetchWithConfig).mockRejectedValueOnce(
        new Error(errorMessage)
      );

      // Act & Assert
      await expect(getUserDetailApi(mockUsername)).rejects.toThrow(
        errorMessage
      );
    });
  });

  describe("getUserProfileApi", () => {
    it("should fetch user profile successfully", async () => {
      // Arrange
      vi.mocked(api.fetchWithConfig).mockResolvedValueOnce(mockUserResponse);

      // Act
      const result = await getUserProfileApi(mockUsername);

      // Assert
      expect(api.fetchWithConfig).toHaveBeenCalledWith(
        `/api/users/${mockUsername}`,
        { method: "GET" }
      );
      expect(result).toEqual(mockUserResponse.user);
    });

    it("should handle API error", async () => {
      // Arrange
      const errorMessage = "API Error";
      vi.mocked(api.fetchWithConfig).mockRejectedValueOnce(
        new Error(errorMessage)
      );

      // Act & Assert
      await expect(getUserProfileApi(mockUsername)).rejects.toThrow(
        errorMessage
      );
    });
  });

  describe("getUserPostsApi", () => {
    it("should fetch user posts successfully", async () => {
      // Arrange
      vi.mocked(api.fetchWithConfig).mockResolvedValueOnce(mockUserResponse);

      // Act
      const result = await getUserPostsApi(mockUsername);

      // Assert
      expect(api.fetchWithConfig).toHaveBeenCalledWith(
        `/api/users/${mockUsername}`,
        { method: "GET" }
      );
      expect(result).toEqual(mockUserResponse.posts);
    });

    it("should return empty array when posts is null", async () => {
      // Arrange
      const responseWithNullPosts = { ...mockUserResponse, posts: null };
      vi.mocked(api.fetchWithConfig).mockResolvedValueOnce(
        responseWithNullPosts
      );

      // Act
      const result = await getUserPostsApi(mockUsername);

      // Assert
      expect(result).toEqual([]);
    });

    it("should handle API error", async () => {
      // Arrange
      const errorMessage = "API Error";
      vi.mocked(api.fetchWithConfig).mockRejectedValueOnce(
        new Error(errorMessage)
      );

      // Act & Assert
      await expect(getUserPostsApi(mockUsername)).rejects.toThrow(errorMessage);
    });
  });
});
