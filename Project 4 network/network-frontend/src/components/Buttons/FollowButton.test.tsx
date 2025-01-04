import { describe, it, vi, expect, beforeEach, Mock } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import FollowButton from "./FollowButton";
import {
  followUserApi,
  unfollowUserApi,
  UserProfile,
} from "../../services/userService";

// Mock the API calls
vi.mock("../../services/userService", () => ({
  followUserApi: vi.fn(),
  unfollowUserApi: vi.fn(),
}));

describe("FollowButton", () => {
  const mockOnFollowingUpdate = vi.fn();

  const createMockUser = (isFollowing: boolean): UserProfile => ({
    username: "testuser",
    email: "test@example.com",
    following_count: 0,
    follower_count: 0,
    is_following: isFollowing,
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders Follow button when user is not following", () => {
    const targetUser = createMockUser(false);
    render(<FollowButton targetUser={targetUser} />);
    expect(screen.getByRole("button")).toHaveTextContent("Follow");
    expect(screen.getByRole("button")).toHaveClass("bg-blue-500");
  });

  it("renders Unfollow button when user is following", () => {
    const targetUser = createMockUser(true);
    render(<FollowButton targetUser={targetUser} />);
    expect(screen.getByRole("button")).toHaveTextContent("Unfollow");
    expect(screen.getByRole("button")).toHaveClass("bg-gray-200");
  });

  it("handles follow action successfully", async () => {
    const targetUser = createMockUser(false);
    const mockFollowApi = followUserApi as Mock;
    mockFollowApi.mockResolvedValueOnce({});

    render(
      <FollowButton
        targetUser={targetUser}
        onFollowingUpdate={mockOnFollowingUpdate}
      />
    );

    const button = screen.getByRole("button");
    fireEvent.click(button);

    // Should show loading state
    expect(button).toHaveTextContent("Loading...");
    expect(button).toBeDisabled();

    // Wait for the API call to resolve
    await waitFor(() => {
      expect(followUserApi).toHaveBeenCalledWith("testuser");
      expect(button).toHaveTextContent("Unfollow");
      expect(mockOnFollowingUpdate).toHaveBeenCalledTimes(1);
    });
  });

  it("handles unfollow action successfully", async () => {
    const targetUser = createMockUser(true);
    const mockUnfollowApi = unfollowUserApi as Mock;
    mockUnfollowApi.mockResolvedValueOnce({});

    render(
      <FollowButton
        targetUser={targetUser}
        onFollowingUpdate={mockOnFollowingUpdate}
      />
    );

    const button = screen.getByRole("button");
    fireEvent.click(button);

    // Should show loading state
    expect(button).toHaveTextContent("Loading...");
    expect(button).toBeDisabled();

    // Wait for the API call to resolve
    await waitFor(() => {
      expect(unfollowUserApi).toHaveBeenCalledWith("testuser");
      expect(button).toHaveTextContent("Follow");
      expect(mockOnFollowingUpdate).toHaveBeenCalledTimes(1);
    });
  });

  it("handles follow API error", async () => {
    const targetUser = createMockUser(false);
    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});
    const mockFollowApi = followUserApi as Mock;
    mockFollowApi.mockRejectedValueOnce(new Error("API Error"));

    render(
      <FollowButton
        targetUser={targetUser}
        onFollowingUpdate={mockOnFollowingUpdate}
      />
    );

    const button = screen.getByRole("button");
    fireEvent.click(button);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Follow action failed:",
        expect.any(Error)
      );
      expect(button).not.toBeDisabled();
      expect(button).toHaveTextContent("Follow");
    });

    consoleErrorSpy.mockRestore();
  });

  it("handles unfollow API error", async () => {
    const targetUser = createMockUser(true);
    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});
    const mockUnfollowApi = unfollowUserApi as Mock;
    mockUnfollowApi.mockRejectedValueOnce(new Error("API Error"));

    render(
      <FollowButton
        targetUser={targetUser}
        onFollowingUpdate={mockOnFollowingUpdate}
      />
    );

    const button = screen.getByRole("button");
    fireEvent.click(button);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Follow action failed:",
        expect.any(Error)
      );
      expect(button).not.toBeDisabled();
      expect(button).toHaveTextContent("Unfollow");
    });

    consoleErrorSpy.mockRestore();
  });

  it("prevents duplicate follow actions", async () => {
    const targetUser = createMockUser(true);
    const mockUnfollowApi = unfollowUserApi as Mock;

    render(<FollowButton targetUser={targetUser} />);
    const button = screen.getByRole("button");

    // 當已經在追蹤狀態時，點擊按鈕應該呼叫 unfollow API
    fireEvent.click(button);
    expect(mockUnfollowApi).toHaveBeenCalledWith("testuser");
  });

  it("prevents duplicate unfollow actions", async () => {
    const targetUser = createMockUser(false);
    const mockFollowApi = followUserApi as Mock;

    render(<FollowButton targetUser={targetUser} />);
    const button = screen.getByRole("button");

    // 當未追蹤時，點擊按鈕應該呼叫 follow API
    fireEvent.click(button);
    expect(mockFollowApi).toHaveBeenCalledWith("testuser");
  });
});
