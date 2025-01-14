import { describe, it, vi, expect, beforeEach, Mock } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Comment } from "./Comment";
import { useAuth } from "../../contexts/AuthContext";
import { useCommentContext } from "../../contexts/CommentContext";
import {
  deleteCommentApi,
  editCommentApi,
  Comment as CommentType,
} from "../../services/commentService";

// Mock the hooks and API calls
vi.mock("../../contexts/AuthContext");
vi.mock("../../contexts/CommentContext");
vi.mock("../../services/commentService");

describe("Comment Component", () => {
  const mockComment: CommentType = {
    id: 1,
    content: "Test comment",
    created_by: "testuser",
    created_at: "2024-01-01T00:00:00Z",
    is_deleted: false,
  };

  const mockTriggerRefresh = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useCommentContext as Mock).mockReturnValue({
      triggerRefresh: mockTriggerRefresh,
    });
  });

  it("renders comment content correctly", () => {
    (useAuth as Mock).mockReturnValue({ user: { username: "otheruser" } });

    render(<Comment comment={mockComment} />);

    expect(screen.getByText("Test comment")).toBeInTheDocument();
    expect(screen.getByText("testuser")).toBeInTheDocument();
    expect(screen.getByText("2024-01-01T00:00:00Z")).toBeInTheDocument();
  });

  it("shows edit and delete buttons for comment author", () => {
    (useAuth as Mock).mockReturnValue({ user: { username: "testuser" } });

    render(<Comment comment={mockComment} />);

    expect(screen.getByText("Edit")).toBeInTheDocument();
    expect(screen.getByText("Delete")).toBeInTheDocument();
  });

  it("hides edit and delete buttons for non-authors", () => {
    (useAuth as Mock).mockReturnValue({ user: { username: "otheruser" } });

    render(<Comment comment={mockComment} />);

    expect(screen.queryByText("Edit")).not.toBeInTheDocument();
    expect(screen.queryByText("Delete")).not.toBeInTheDocument();
  });

  it("shows textarea when edit mode is activated", () => {
    (useAuth as Mock).mockReturnValue({ user: { username: "testuser" } });

    render(<Comment comment={mockComment} />);

    fireEvent.click(screen.getByText("Edit"));

    const textarea = screen.getByRole("textbox");
    expect(textarea).toBeInTheDocument();
    expect(textarea).toHaveValue("Test comment");
    expect(screen.getByText("Save")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("handles edit cancellation correctly", () => {
    (useAuth as Mock).mockReturnValue({ user: { username: "testuser" } });

    render(<Comment comment={mockComment} />);

    fireEvent.click(screen.getByText("Edit"));
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "Changed comment" } });
    fireEvent.click(screen.getByText("Cancel"));

    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.getByText("Test comment")).toBeInTheDocument();
  });

  it("handles successful edit submission", async () => {
    (useAuth as Mock).mockReturnValue({ user: { username: "testuser" } });
    let savedCallback: (() => void) | undefined;
    (editCommentApi as Mock).mockImplementation(
      (_id, _content, callback: () => void) => {
        savedCallback = callback;
        return Promise.resolve({});
      }
    );

    render(<Comment comment={mockComment} />);

    fireEvent.click(screen.getByText("Edit"));
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "Updated comment" } });
    fireEvent.click(screen.getByText("Save"));

    await waitFor(() => {
      expect(editCommentApi).toHaveBeenCalledWith(
        1,
        "Updated comment",
        expect.any(Function)
      );
    });

    savedCallback?.();

    expect(mockTriggerRefresh).toHaveBeenCalledWith("EDIT");
  });

  it("handles edit submission error", async () => {
    (useAuth as Mock).mockReturnValue({ user: { username: "testuser" } });
    const mockError = new Error("Edit failed");
    (editCommentApi as Mock).mockRejectedValue(mockError);
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(<Comment comment={mockComment} />);

    fireEvent.click(screen.getByText("Edit"));
    fireEvent.click(screen.getByText("Save"));

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        "Failed to edit comment:",
        mockError
      );
    });

    consoleSpy.mockRestore();
  });

  it("handles successful deletion", async () => {
    (useAuth as Mock).mockReturnValue({ user: { username: "testuser" } });
    let savedCallback: (() => void) | undefined;
    (deleteCommentApi as Mock).mockImplementation(
      (_id, callback: () => void) => {
        savedCallback = callback;
        return Promise.resolve({});
      }
    );

    render(<Comment comment={mockComment} />);

    fireEvent.click(screen.getByText("Delete"));

    await waitFor(() => {
      expect(deleteCommentApi).toHaveBeenCalledWith(1, expect.any(Function));
    });

    savedCallback?.();

    expect(mockTriggerRefresh).toHaveBeenCalledWith("DELETE");
  });

  it("handles deletion error", async () => {
    (useAuth as Mock).mockReturnValue({ user: { username: "testuser" } });
    const mockError = new Error("Delete failed");
    (deleteCommentApi as Mock).mockRejectedValue(mockError);
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(<Comment comment={mockComment} />);

    fireEvent.click(screen.getByText("Delete"));

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        "Failed to delete comment:",
        mockError
      );
    });

    consoleSpy.mockRestore();
  });
});
