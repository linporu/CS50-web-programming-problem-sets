import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CreateComment } from "./CreateComment";
import * as commentService from "../../services/commentService";

// Mock the commentService
vi.mock("../../services/commentService", () => ({
  createCommentApi: vi.fn(),
}));

// Mock the CommentContext
const mockTriggerRefresh = vi.fn();
vi.mock("../../contexts/CommentContext", () => ({
  useCommentContext: () => ({
    triggerRefresh: mockTriggerRefresh,
  }),
}));

describe("CreateComment", () => {
  const mockPostId = 1;
  const mockOnCommentCreated = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the comment form correctly", () => {
    render(<CreateComment postId={mockPostId} />);

    expect(
      screen.getByPlaceholderText("Write a comment...")
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Comment" })).toBeInTheDocument();
  });

  it("shows error when submitting empty comment", async () => {
    render(<CreateComment postId={mockPostId} />);

    const submitButton = screen.getByRole("button", { name: "Comment" });
    await userEvent.click(submitButton);

    expect(screen.getByText("Comment cannot be empty")).toBeInTheDocument();
    expect(commentService.createCommentApi).not.toHaveBeenCalled();
  });

  it("successfully creates a comment", async () => {
    vi.mocked(commentService.createCommentApi).mockImplementation(
      async (_, __, callback) => {
        callback?.();
        return { message: "Comment created successfully" };
      }
    );

    render(
      <CreateComment
        postId={mockPostId}
        onCommentCreated={mockOnCommentCreated}
      />
    );

    const textarea = screen.getByPlaceholderText("Write a comment...");
    const submitButton = screen.getByRole("button", { name: "Comment" });

    await userEvent.type(textarea, "Test comment");
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(commentService.createCommentApi).toHaveBeenCalledWith(
        mockPostId,
        "Test comment",
        expect.any(Function)
      );
      expect(mockTriggerRefresh).toHaveBeenCalledWith("CREATE");
      expect(mockOnCommentCreated).toHaveBeenCalled();
      expect(textarea).toHaveValue("");
    });
  });

  it("handles API error when creating comment", async () => {
    const errorMessage = "Network error";
    vi.mocked(commentService.createCommentApi).mockRejectedValue(
      new Error(errorMessage)
    );

    render(<CreateComment postId={mockPostId} />);

    const textarea = screen.getByPlaceholderText("Write a comment...");
    const submitButton = screen.getByRole("button", { name: "Comment" });

    await userEvent.type(textarea, "Test comment");
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(`Failed to create comment: ${errorMessage}`)
      ).toBeInTheDocument();
      expect(textarea).toHaveValue("Test comment"); // Content should remain
    });
  });

  it("updates textarea value on user input", async () => {
    render(<CreateComment postId={mockPostId} />);

    const textarea = screen.getByPlaceholderText("Write a comment...");
    await userEvent.type(textarea, "Hello");

    expect(textarea).toHaveValue("Hello");
  });

  it("clears error message when starting to type after an error", async () => {
    render(<CreateComment postId={mockPostId} />);

    // First trigger an error
    const submitButton = screen.getByRole("button", { name: "Comment" });
    await userEvent.click(submitButton);
    expect(screen.getByText("Comment cannot be empty")).toBeInTheDocument();

    // Then start typing
    const textarea = screen.getByPlaceholderText("Write a comment...");
    await userEvent.type(textarea, "New comment");

    // Error should be gone
    expect(
      screen.queryByText("Comment cannot be empty")
    ).not.toBeInTheDocument();
  });
});
