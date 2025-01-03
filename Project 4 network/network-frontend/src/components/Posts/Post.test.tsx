import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import Post from "./Post";
import { AuthContext } from "@/contexts/AuthContext";
import { editPostApi, deletePostApi } from "@/services/postService";

// Mock the post service
vi.mock("@/services/postService", () => ({
  editPostApi: vi.fn(),
  deletePostApi: vi.fn(),
}));

describe("Post Component", () => {
  const mockPostProps = {
    id: 1,
    content: "Test post content",
    created_by: "testuser",
    created_at: "2024-03-20T10:00:00Z",
    updated_at: "",
    is_deleted: false,
    likes_count: 5,
    comments_count: 3,
    comments: [
      {
        id: 1,
        content: "Test comment",
        created_by: "commenter",
        created_at: "2024-03-20T10:01:00Z",
        is_deleted: false,
      },
    ],
    onPostUpdate: vi.fn(),
  };

  const renderWithAuth = (
    component: React.ReactNode,
    authUser: { username: string } | null = null
  ) => {
    const fullUser = authUser
      ? {
          id: 1,
          username: authUser.username,
          email: "test@example.com",
          following_count: 0,
          follower_count: 0,
        }
      : null;

    return render(
      <AuthContext.Provider
        value={{
          user: fullUser,
          setUser: vi.fn(),
          isAuthenticated: !!fullUser,
          clearAuth: vi.fn(),
          _isDefault: false,
        }}
      >
        <BrowserRouter>{component}</BrowserRouter>
      </AuthContext.Provider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Basic Rendering", () => {
    it("renders post content correctly", () => {
      renderWithAuth(<Post {...mockPostProps} />);
      expect(screen.getByText("Test post content")).toBeInTheDocument();
      expect(screen.getByText("testuser")).toBeInTheDocument();
    });

    it("renders username as a link to profile page", () => {
      renderWithAuth(<Post {...mockPostProps} />);
      const usernameLink = screen.getByRole("link", { name: "testuser" });
      expect(usernameLink).toBeInTheDocument();
      expect(usernameLink).toHaveAttribute("href", "/profile/testuser");
    });

    it("shows created_at when updated_at is empty", () => {
      renderWithAuth(<Post {...mockPostProps} />);
      expect(screen.getByText("2024-03-20T10:00:00Z")).toBeInTheDocument();
    });

    it("shows updated_at when available", () => {
      const updatedProps = {
        ...mockPostProps,
        updated_at: "2024-03-20T11:00:00Z",
      };
      renderWithAuth(<Post {...updatedProps} />);
      expect(screen.getByText("2024-03-20T11:00:00Z")).toBeInTheDocument();
    });

    it("displays correct likes and comments count", () => {
      renderWithAuth(<Post {...mockPostProps} />);
      const likeButton = screen.getByRole("button", { name: /like/i });
      const commentButton = screen.getByRole("button", { name: /comment/i });

      expect(likeButton).toHaveTextContent("5");
      expect(commentButton).toHaveTextContent("3");
    });

    it("renders like and comment buttons with correct styling", () => {
      renderWithAuth(<Post {...mockPostProps} />);
      const likeButton = screen.getByRole("button", { name: /like/i });
      const commentButton = screen.getByRole("button", { name: /comment/i });

      expect(likeButton).toHaveClass("hover:text-blue-500");
      expect(commentButton).toHaveClass("hover:text-blue-500");
    });
  });

  describe("Post Creator Actions", () => {
    it("shows edit and delete buttons when user is post creator", () => {
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });
      expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Delete" })
      ).toBeInTheDocument();
    });

    it("does not show edit and delete buttons when user is not post creator", () => {
      renderWithAuth(<Post {...mockPostProps} />, { username: "otheruser" });
      expect(screen.queryByRole("button", { name: "Edit" })).toBeNull();
      expect(screen.queryByRole("button", { name: "Delete" })).toBeNull();
    });

    it("shows edit and delete buttons with correct styling", () => {
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });
      const editButton = screen.getByRole("button", { name: "Edit" });
      const deleteButton = screen.getByRole("button", { name: "Delete" });

      expect(editButton).toHaveClass(
        "text-sm",
        "text-gray-600",
        "hover:text-blue-500"
      );
      expect(deleteButton).toHaveClass(
        "text-sm",
        "text-gray-600",
        "hover:text-blue-500"
      );
    });
  });

  describe("Edit Functionality", () => {
    it("enters edit mode when edit button is clicked", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      await user.click(screen.getByRole("button", { name: "Edit" }));
      const textarea = screen.getByRole("textbox");
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveValue("Test post content");
      expect(textarea).toHaveClass(
        "w-full",
        "p-2",
        "border",
        "border-gray-300",
        "rounded-md"
      );
    });

    it("shows error when trying to save empty content", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      await user.click(screen.getByRole("button", { name: "Edit" }));
      const textarea = screen.getByRole("textbox");
      await user.clear(textarea);
      await user.click(screen.getByRole("button", { name: "Save" }));

      const errorMessage = screen.getByText("Content cannot be empty");
      expect(errorMessage).toBeInTheDocument();
      expect(errorMessage).toHaveClass("text-sm", "text-red-500");
    });

    it("shows error when content is unchanged", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      await user.click(screen.getByRole("button", { name: "Edit" }));
      await user.click(screen.getByRole("button", { name: "Save" }));

      const errorMessage = screen.getByText(
        "No changes were made to the post content"
      );
      expect(errorMessage).toBeInTheDocument();
      expect(errorMessage).toHaveClass("text-sm", "text-red-500");
    });

    it("successfully saves edited content", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      await user.click(screen.getByRole("button", { name: "Edit" }));
      const textarea = screen.getByRole("textbox");
      await user.clear(textarea);
      await user.type(textarea, "Updated content");

      (editPostApi as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        message: "Success",
      });

      await user.click(screen.getByRole("button", { name: "Save" }));
      expect(editPostApi).toHaveBeenCalledWith(1, "Updated content");
      expect(mockPostProps.onPostUpdate).toHaveBeenCalled();
    });

    it("handles edit API error correctly", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      await user.click(screen.getByRole("button", { name: "Edit" }));
      const textarea = screen.getByRole("textbox");
      await user.clear(textarea);
      await user.type(textarea, "Updated content");

      const errorMessage = "Failed to update";
      (editPostApi as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error(errorMessage)
      );

      await user.click(screen.getByRole("button", { name: "Save" }));
      const error = screen.getByText(`Failed to update post: ${errorMessage}`);
      expect(error).toBeInTheDocument();
      expect(error).toHaveClass("text-sm", "text-red-500");
    });

    it("cancels edit mode correctly", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      await user.click(screen.getByRole("button", { name: "Edit" }));
      await user.click(screen.getByRole("button", { name: "Cancel" }));

      expect(screen.queryByRole("textbox")).toBeNull();
      expect(screen.getByText("Test post content")).toBeInTheDocument();
    });

    it("renders edit mode buttons with correct styling", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      await user.click(screen.getByRole("button", { name: "Edit" }));

      const saveButton = screen.getByRole("button", { name: "Save" });
      const cancelButton = screen.getByRole("button", { name: "Cancel" });

      expect(saveButton).toHaveClass(
        "px-3",
        "py-1",
        "text-sm",
        "text-white",
        "bg-blue-500",
        "rounded",
        "hover:bg-blue-600"
      );
      expect(cancelButton).toHaveClass(
        "px-3",
        "py-1",
        "text-sm",
        "text-gray-600",
        "border",
        "border-gray-300",
        "rounded",
        "hover:bg-gray-100"
      );
    });
  });

  describe("Delete Functionality", () => {
    it("successfully deletes post", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      (deletePostApi as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        message: "Success",
      });

      await user.click(screen.getByRole("button", { name: "Delete" }));
      expect(deletePostApi).toHaveBeenCalledWith(1);
      expect(mockPostProps.onPostUpdate).toHaveBeenCalled();
    });

    it("handles delete API error correctly", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      const errorMessage = "Failed to delete";
      (deletePostApi as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error(errorMessage)
      );

      await user.click(screen.getByRole("button", { name: "Delete" }));
      const error = screen.getByText(`Failed to delete post: ${errorMessage}`);
      expect(error).toBeInTheDocument();
      expect(error).toHaveClass("text-sm", "text-red-500");
    });
  });
});
