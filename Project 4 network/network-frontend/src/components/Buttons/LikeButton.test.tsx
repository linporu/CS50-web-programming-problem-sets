import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import LikeButton from "./LikeButton";
import { likePostApi, unLikePostApi } from "../../services/postService";

// Mock the API calls
vi.mock("../../services/postService", () => ({
  likePostApi: vi.fn(),
  unLikePostApi: vi.fn(),
}));

describe("LikeButton", () => {
  const mockOnLikeUpdate = vi.fn();
  const defaultProps = {
    postId: 1,
    initialIsLiked: false,
    likesCount: 10,
    onLikeUpdate: mockOnLikeUpdate,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders initial state correctly when not liked", () => {
    render(<LikeButton {...defaultProps} />);

    expect(screen.getByText("Like")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByRole("button")).toHaveClass("text-gray-600");
  });

  it("renders initial state correctly when liked", () => {
    render(<LikeButton {...defaultProps} initialIsLiked={true} />);

    expect(screen.getByText("Unlike")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByRole("button")).toHaveClass("text-blue-500");
  });

  it("handles like action successfully", async () => {
    vi.mocked(likePostApi).mockResolvedValueOnce({
      message: "Post liked successfully",
    });

    render(<LikeButton {...defaultProps} />);

    const button = screen.getByRole("button");
    fireEvent.click(button);

    // Check loading state
    expect(screen.getByText("Loading...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Unlike")).toBeInTheDocument();
      expect(screen.getByText("11")).toBeInTheDocument();
    });

    expect(likePostApi).toHaveBeenCalledWith(1);
    expect(mockOnLikeUpdate).toHaveBeenCalledWith(10, true);
  });

  it("handles unlike action successfully", async () => {
    vi.mocked(unLikePostApi).mockResolvedValueOnce({
      message: "Post unliked successfully",
    });

    render(<LikeButton {...defaultProps} initialIsLiked={true} />);

    const button = screen.getByRole("button");
    fireEvent.click(button);

    // Check loading state
    expect(screen.getByText("Loading...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Like")).toBeInTheDocument();
      expect(screen.getByText("9")).toBeInTheDocument();
    });

    expect(unLikePostApi).toHaveBeenCalledWith(1);
    expect(mockOnLikeUpdate).toHaveBeenCalledWith(10, false);
  });

  it("handles API error gracefully", async () => {
    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});
    vi.mocked(likePostApi).mockRejectedValueOnce(new Error("API Error"));

    render(<LikeButton {...defaultProps} />);

    const button = screen.getByRole("button");
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText("Like")).toBeInTheDocument();
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Like action failed:",
        expect.any(Error)
      );
    });

    expect(button).not.toBeDisabled();
    consoleErrorSpy.mockRestore();
  });

  it("disables button during loading state", async () => {
    vi.mocked(likePostApi).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(() => resolve({ message: "Post liked successfully" }), 100)
        )
    );

    render(<LikeButton {...defaultProps} />);

    const button = screen.getByRole("button");
    fireEvent.click(button);

    expect(button).toBeDisabled();
    expect(screen.getByText("Loading...")).toBeInTheDocument();

    await waitFor(() => {
      expect(button).not.toBeDisabled();
    });
  });
});
