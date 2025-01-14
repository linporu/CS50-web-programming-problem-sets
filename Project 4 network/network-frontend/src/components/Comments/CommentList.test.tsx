import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { CommentList } from "./CommentList";
import * as CommentContext from "../../contexts/CommentContext";
import { Comment } from "../../services/commentService";

// Mock the Comment component
vi.mock("./Comment", () => ({
  Comment: ({ comment }: { comment: Comment }) => (
    <div data-testid={`comment-${comment.id}`}>{comment.content}</div>
  ),
}));

describe("CommentList", () => {
  // Mock data
  const mockComments: Comment[] = [
    {
      id: 1,
      content: "Test comment 1",
      created_by: "user1",
      created_at: "2024-01-01T00:00:00Z",
      is_deleted: false,
    },
    {
      id: 2,
      content: "Test comment 2",
      created_by: "user2",
      created_at: "2024-01-02T00:00:00Z",
      is_deleted: false,
    },
  ];

  it("should show loading state when isLoading is true", () => {
    vi.spyOn(CommentContext, "useCommentContext").mockReturnValue({
      comments: [],
      isLoading: true,
      triggerRefresh: vi.fn(),
    });

    render(<CommentList />);
    expect(screen.getByText("Loading comments...")).toBeInTheDocument();
  });

  it("should render comments when data is loaded", () => {
    vi.spyOn(CommentContext, "useCommentContext").mockReturnValue({
      comments: mockComments,
      isLoading: false,
      triggerRefresh: vi.fn(),
    });

    render(<CommentList />);

    mockComments.forEach((comment) => {
      expect(screen.getByTestId(`comment-${comment.id}`)).toBeInTheDocument();
      expect(screen.getByText(comment.content)).toBeInTheDocument();
    });
  });

  it("should render empty list when no comments are available", () => {
    vi.spyOn(CommentContext, "useCommentContext").mockReturnValue({
      comments: [],
      isLoading: false,
      triggerRefresh: vi.fn(),
    });

    const { container } = render(<CommentList />);
    const commentContainer = container.firstChild;

    expect(commentContainer).toBeEmptyDOMElement();
  });

  it("should handle error when context is not provided", () => {
    vi.spyOn(CommentContext, "useCommentContext").mockImplementation(() => {
      throw new Error(
        "useCommentContext must be used within a CommentProvider"
      );
    });

    expect(() => render(<CommentList />)).toThrow(
      "useCommentContext must be used within a CommentProvider"
    );
  });
});
