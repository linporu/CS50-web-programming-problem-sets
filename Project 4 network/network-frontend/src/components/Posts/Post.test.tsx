import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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
        {component}
      </AuthContext.Provider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Basic Rendering", () => {
    it("renders post content correctly", () => {
      renderWithAuth(<Post {...mockPostProps} />);
      expect(screen.getByText("Test post content")).toBeDefined();
      expect(screen.getByText("testuser")).toBeDefined();
    });

    it("shows created_at when updated_at is empty", () => {
      renderWithAuth(<Post {...mockPostProps} />);
      expect(screen.getByText("2024-03-20T10:00:00Z")).toBeDefined();
    });

    it("shows updated_at when available", () => {
      const updatedProps = {
        ...mockPostProps,
        updated_at: "2024-03-20T11:00:00Z",
      };
      renderWithAuth(<Post {...updatedProps} />);
      expect(screen.getByText("2024-03-20T11:00:00Z")).toBeDefined();
    });

    it("displays correct likes and comments count", () => {
      renderWithAuth(<Post {...mockPostProps} />);
      expect(screen.getByText("5")).toBeDefined();
      expect(screen.getByText("3")).toBeDefined();
    });
  });

  describe("Post Creator Actions", () => {
    it("shows edit and delete buttons when user is post creator", () => {
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });
      expect(screen.getByText("Edit")).toBeDefined();
      expect(screen.getByText("Delete")).toBeDefined();
    });

    it("does not show edit and delete buttons when user is not post creator", () => {
      renderWithAuth(<Post {...mockPostProps} />, { username: "otheruser" });
      expect(screen.queryByText("Edit")).toBeNull();
      expect(screen.queryByText("Delete")).toBeNull();
    });
  });

  describe("Edit Functionality", () => {
    it("enters edit mode when edit button is clicked", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      await user.click(screen.getByText("Edit"));
      expect(screen.getByRole("textbox")).toHaveValue("Test post content");
    });

    it("shows error when trying to save empty content", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      await user.click(screen.getByText("Edit"));
      const textarea = screen.getByRole("textbox");
      await user.clear(textarea);
      await user.click(screen.getByText("Save"));

      expect(screen.getByText("Content cannot be empty")).toBeDefined();
    });

    it("shows error when content is unchanged", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      await user.click(screen.getByText("Edit"));
      await user.click(screen.getByText("Save"));

      expect(
        screen.getByText("No changes were made to the post content")
      ).toBeDefined();
    });

    it("successfully saves edited content", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      await user.click(screen.getByText("Edit"));
      const textarea = screen.getByRole("textbox");
      await user.clear(textarea);
      await user.type(textarea, "Updated content");

      (editPostApi as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        message: "Success",
      });

      await user.click(screen.getByText("Save"));
      expect(editPostApi).toHaveBeenCalledWith(1, "Updated content");
      expect(mockPostProps.onPostUpdate).toHaveBeenCalled();
    });

    it("handles edit API error correctly", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      await user.click(screen.getByText("Edit"));
      const textarea = screen.getByRole("textbox");
      await user.clear(textarea);
      await user.type(textarea, "Updated content");

      const errorMessage = "Failed to update";
      (editPostApi as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error(errorMessage)
      );

      await user.click(screen.getByText("Save"));
      expect(
        screen.getByText(`Failed to update post: ${errorMessage}`)
      ).toBeDefined();
    });

    it("cancels edit mode correctly", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      await user.click(screen.getByText("Edit"));
      await user.click(screen.getByText("Cancel"));

      expect(screen.queryByRole("textbox")).toBeNull();
      expect(screen.getByText("Test post content")).toBeDefined();
    });
  });

  describe("Delete Functionality", () => {
    it("successfully deletes post", async () => {
      const user = userEvent.setup();
      renderWithAuth(<Post {...mockPostProps} />, { username: "testuser" });

      (deletePostApi as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        message: "Success",
      });

      await user.click(screen.getByText("Delete"));
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

      await user.click(screen.getByText("Delete"));
      expect(
        screen.getByText(`Failed to delete post: ${errorMessage}`)
      ).toBeDefined();
    });
  });
});
