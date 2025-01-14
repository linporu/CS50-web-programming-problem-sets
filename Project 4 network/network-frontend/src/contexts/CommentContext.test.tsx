import { describe, it, expect, vi, beforeEach, Mock } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { CommentProvider, useCommentContext } from "./CommentContext";
import * as commentService from "../services/commentService";
import { Comment } from "../services/commentService";

// Mock the commentService
vi.mock("../services/commentService", () => ({
  getCommentsApi: vi.fn(),
}));

describe("CommentContext", () => {
  const mockPostId = 1;
  const mockOnCommentCreate = vi.fn();
  const mockComments: Comment[] = [
    { id: 1, content: "Test Comment 1" } as Comment,
    { id: 2, content: "Test Comment 2" } as Comment,
  ];

  // Helper function to wrap component with provider
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <CommentProvider postId={mockPostId} onCommentCreate={mockOnCommentCreate}>
      {children}
    </CommentProvider>
  );

  beforeEach(() => {
    vi.clearAllMocks();
    (commentService.getCommentsApi as Mock).mockResolvedValue(mockComments);
  });

  it("should throw error when useCommentContext is used outside of provider", () => {
    expect(() => renderHook(() => useCommentContext())).toThrow(
      "useCommentContext must be used within a CommentProvider"
    );
  });

  it("should fetch comments on mount", async () => {
    const { result } = renderHook(() => useCommentContext(), { wrapper });

    // Wait for the initial fetch to complete
    await act(async () => {
      await Promise.resolve();
    });

    expect(commentService.getCommentsApi).toHaveBeenCalledWith(mockPostId);
    expect(result.current.comments).toEqual(mockComments);
    expect(result.current.isLoading).toBe(false);
  });

  it("should handle fetch error gracefully", async () => {
    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});
    (commentService.getCommentsApi as Mock).mockRejectedValue(
      new Error("Fetch failed")
    );

    const { result } = renderHook(() => useCommentContext(), { wrapper });

    await act(async () => {
      await Promise.resolve();
    });

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      "Failed to fetch comments:",
      expect.any(Error)
    );
    expect(result.current.comments).toEqual([]);
    expect(result.current.isLoading).toBe(false);

    consoleErrorSpy.mockRestore();
  });

  it("should handle CREATE action in triggerRefresh", async () => {
    const { result } = renderHook(() => useCommentContext(), { wrapper });

    await act(async () => {
      await result.current.triggerRefresh("CREATE");
    });

    expect(mockOnCommentCreate).toHaveBeenCalled();
    expect(commentService.getCommentsApi).toHaveBeenCalledTimes(2); // Initial + refresh
  });

  it("should handle EDIT action in triggerRefresh", async () => {
    const { result } = renderHook(() => useCommentContext(), { wrapper });

    await act(async () => {
      await result.current.triggerRefresh("EDIT");
    });

    expect(mockOnCommentCreate).not.toHaveBeenCalled();
    expect(commentService.getCommentsApi).toHaveBeenCalledTimes(2); // Initial + refresh
  });

  it("should handle DELETE action in triggerRefresh", async () => {
    const { result } = renderHook(() => useCommentContext(), { wrapper });

    await act(async () => {
      await result.current.triggerRefresh("DELETE");
    });

    expect(mockOnCommentCreate).not.toHaveBeenCalled();
    expect(commentService.getCommentsApi).toHaveBeenCalledTimes(2); // Initial + refresh
  });

  it("should update loading state during fetch", async () => {
    let resolvePromise: (value: Comment[]) => void;
    const promise = new Promise<Comment[]>((resolve) => {
      resolvePromise = resolve;
    });

    (commentService.getCommentsApi as Mock).mockImplementation(() => promise);

    const { result } = renderHook(() => useCommentContext(), { wrapper });

    // Check initial loading state
    expect(result.current.isLoading).toBe(true);

    // Resolve the promise
    await act(async () => {
      resolvePromise(mockComments);
      await promise;
    });

    // Check final loading state
    expect(result.current.isLoading).toBe(false);
  });
});
