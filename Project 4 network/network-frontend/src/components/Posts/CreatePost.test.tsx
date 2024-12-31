import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CreatePost } from "./CreatePost";
import { createPostApi } from "../../services/postService";

// Mock the postService
vi.mock("../../services/postService", () => ({
  createPostApi: vi.fn(),
}));

describe("CreatePost", () => {
  const mockOnPostCreated = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the create post form", () => {
    render(<CreatePost onPostCreated={mockOnPostCreated} />);

    expect(
      screen.getByPlaceholderText("What's on your mind?")
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Post" })).toBeInTheDocument();
  });

  it("handles empty content submission", async () => {
    render(<CreatePost onPostCreated={mockOnPostCreated} />);

    const submitButton = screen.getByRole("button", { name: "Post" });
    await userEvent.click(submitButton);

    expect(screen.getByText("Content cannot be empty")).toBeInTheDocument();
    expect(createPostApi).not.toHaveBeenCalled();
    expect(mockOnPostCreated).not.toHaveBeenCalled();
  });

  it("successfully creates a post", async () => {
    const testContent = "Test post content";
    vi.mocked(createPostApi).mockResolvedValueOnce({
      message: "Post created successfully",
    });

    render(<CreatePost onPostCreated={mockOnPostCreated} />);

    const textarea = screen.getByPlaceholderText("What's on your mind?");
    await userEvent.type(textarea, testContent);

    const submitButton = screen.getByRole("button", { name: "Post" });
    await userEvent.click(submitButton);

    expect(createPostApi).toHaveBeenCalledWith(testContent);
    expect(mockOnPostCreated).toHaveBeenCalledOnce();
    expect(textarea).toHaveValue("");
    expect(submitButton).toBeEnabled();
  });

  it("handles API error during post creation", async () => {
    const errorMessage = "Network error";
    vi.mocked(createPostApi).mockRejectedValueOnce(new Error(errorMessage));

    render(<CreatePost onPostCreated={mockOnPostCreated} />);

    const textarea = screen.getByPlaceholderText("What's on your mind?");
    await userEvent.type(textarea, "Test content");

    const submitButton = screen.getByRole("button", { name: "Post" });
    await userEvent.click(submitButton);

    expect(await screen.findByText(errorMessage)).toBeInTheDocument();
    expect(mockOnPostCreated).not.toHaveBeenCalled();
    expect(submitButton).toBeEnabled();
  });

  it("disables form elements while submitting", async () => {
    vi.mocked(createPostApi).mockImplementationOnce(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(<CreatePost onPostCreated={mockOnPostCreated} />);

    const textarea = screen.getByPlaceholderText("What's on your mind?");
    await userEvent.type(textarea, "Test content");

    const submitButton = screen.getByRole("button", { name: "Post" });
    await userEvent.click(submitButton);

    expect(textarea).toBeDisabled();
    expect(screen.getByText("Posting...")).toBeInTheDocument();

    await waitFor(() => {
      expect(textarea).not.toBeDisabled();
      expect(screen.getByText("Post")).toBeInTheDocument();
    });
  });
});
