import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  createCommentApi,
  editCommentApi,
  deleteCommentApi,
  getCommentsApi,
  type Comment,
} from "./commentService";
import * as api from "./api";

// Mock the api module
vi.mock("./api", () => ({
  fetchWithConfig: vi.fn(),
}));

describe("commentService", () => {
  const mockComment: Comment = {
    id: 1,
    content: "Test comment",
    created_by: "testuser",
    created_at: "2024-03-20T12:00:00Z",
    is_deleted: false,
  };

  const mockSuccessResponse = { message: "Success" };
  const mockErrorResponse = { error: "Error occurred" };
  const mockOnSuccess = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("createCommentApi", () => {
    it("should create a comment successfully", async () => {
      vi.mocked(api.fetchWithConfig).mockResolvedValueOnce(mockSuccessResponse);

      const result = await createCommentApi(1, "Test comment", mockOnSuccess);

      expect(api.fetchWithConfig).toHaveBeenCalledWith(
        "/api/posts/1/comments",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: "Test comment" }),
        }
      );
      expect(result).toEqual(mockSuccessResponse);
      expect(mockOnSuccess).toHaveBeenCalled();
    });

    it("should handle error when creating comment fails", async () => {
      vi.mocked(api.fetchWithConfig).mockResolvedValueOnce(mockErrorResponse);

      await expect(createCommentApi(1, "Test comment")).rejects.toThrow(
        "Error occurred"
      );
      expect(mockOnSuccess).not.toHaveBeenCalled();
    });
  });

  describe("editCommentApi", () => {
    it("should edit a comment successfully", async () => {
      vi.mocked(api.fetchWithConfig).mockResolvedValueOnce(mockSuccessResponse);

      const result = await editCommentApi(1, "Updated comment", mockOnSuccess);

      expect(api.fetchWithConfig).toHaveBeenCalledWith("/api/comment/1", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: "Updated comment" }),
      });
      expect(result).toEqual(mockSuccessResponse);
      expect(mockOnSuccess).toHaveBeenCalled();
    });

    it("should handle error when editing comment fails", async () => {
      vi.mocked(api.fetchWithConfig).mockResolvedValueOnce(mockErrorResponse);

      await expect(editCommentApi(1, "Updated comment")).rejects.toThrow(
        "Error occurred"
      );
      expect(mockOnSuccess).not.toHaveBeenCalled();
    });
  });

  describe("deleteCommentApi", () => {
    it("should delete a comment successfully", async () => {
      vi.mocked(api.fetchWithConfig).mockResolvedValueOnce(mockSuccessResponse);

      const result = await deleteCommentApi(1, mockOnSuccess);

      expect(api.fetchWithConfig).toHaveBeenCalledWith("/api/comment/1", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
      });
      expect(result).toEqual(mockSuccessResponse);
      expect(mockOnSuccess).toHaveBeenCalled();
    });

    it("should handle error when deleting comment fails", async () => {
      vi.mocked(api.fetchWithConfig).mockResolvedValueOnce(mockErrorResponse);

      await expect(deleteCommentApi(1)).rejects.toThrow("Error occurred");
      expect(mockOnSuccess).not.toHaveBeenCalled();
    });
  });

  describe("getCommentsApi", () => {
    it("should get comments successfully", async () => {
      const mockComments = { comments: [mockComment] };
      vi.mocked(api.fetchWithConfig).mockResolvedValueOnce(mockComments);

      const result = await getCommentsApi(1);

      expect(api.fetchWithConfig).toHaveBeenCalledWith(
        "/api/posts/1/comments",
        {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        }
      );
      expect(result).toEqual([mockComment]);
    });

    it("should handle error when getting comments fails", async () => {
      vi.mocked(api.fetchWithConfig).mockResolvedValueOnce(mockErrorResponse);

      await expect(getCommentsApi(1)).rejects.toThrow("Error occurred");
    });
  });
});
