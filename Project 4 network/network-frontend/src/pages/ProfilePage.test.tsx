import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ProfilePage from "./ProfilePage";
import * as userService from "../services/userService";
import { AuthContext } from "../contexts/AuthContext";
import { UserProfile } from "../services/userService";

// Mock the userService
vi.mock("../services/userService");
// Mock the PostList component
vi.mock("../components/Posts/PostList", () => ({
  default: () => <div data-testid="post-list">PostList Component</div>,
}));
// Mock the FollowButton component
vi.mock("../components/Buttons/FollowButton", () => ({
  default: ({
    onFollowingUpdate,
  }: {
    targetUser: UserProfile;
    onFollowingUpdate: () => void;
  }) => (
    <button data-testid="follow-button" onClick={onFollowingUpdate}>
      Follow Button
    </button>
  ),
}));

const mockProfile = {
  username: "testuser",
  email: "test@example.com",
  following_count: 10,
  follower_count: 20,
  is_following: false,
};

interface TestUser {
  id: number;
  username: string;
  email: string;
  following_count: number;
  follower_count: number;
}

describe("ProfilePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderProfilePage = (
    username: string = "testuser",
    authUser: TestUser | null = null
  ) => {
    return render(
      <AuthContext.Provider
        value={{
          user: authUser,
          setUser: vi.fn(),
          isAuthenticated: !!authUser,
          clearAuth: vi.fn(),
          loading: false,
        }}
      >
        <MemoryRouter initialEntries={[`/profile/${username}`]}>
          <Routes>
            <Route path="/profile/:username" element={<ProfilePage />} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );
  };

  it("should render user profile data successfully", async () => {
    // Mock the API call
    vi.mocked(userService.getUserProfileApi).mockResolvedValueOnce(mockProfile);

    renderProfilePage();

    // Verify loading state
    expect(screen.queryByText(mockProfile.username)).not.toBeInTheDocument();

    // Wait for the profile data to load
    await waitFor(() => {
      expect(screen.getByText(mockProfile.username)).toBeInTheDocument();
    });

    // Verify profile information is displayed
    expect(
      screen.getByText(`Followers: ${mockProfile.follower_count}`)
    ).toBeInTheDocument();
    expect(
      screen.getByText(`Following: ${mockProfile.following_count}`)
    ).toBeInTheDocument();

    // Verify PostList is rendered
    expect(screen.getByTestId("post-list")).toBeInTheDocument();
  });

  it("should handle API error gracefully", async () => {
    // Mock the API call to throw an error
    vi.mocked(userService.getUserProfileApi).mockRejectedValueOnce(
      new Error("Failed to fetch")
    );

    // Spy on console.error
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    renderProfilePage();

    // Wait for the error to be logged
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });

    // Clean up
    consoleSpy.mockRestore();
  });

  it("should return null when username is not provided", () => {
    renderProfilePage("");

    expect(screen.queryByTestId("post-list")).not.toBeInTheDocument();
  });

  it("should fetch new profile when username changes", async () => {
    const getUserProfileApiMock = vi.mocked(userService.getUserProfileApi);

    const user1Profile = { ...mockProfile, username: "user1" };
    const user2Profile = { ...mockProfile, username: "user2" };

    getUserProfileApiMock
      .mockResolvedValueOnce(user1Profile)
      .mockResolvedValueOnce(user2Profile);

    const { unmount } = renderProfilePage("user1");

    await waitFor(() => {
      expect(getUserProfileApiMock).toHaveBeenCalledWith("user1");
    });

    unmount();

    renderProfilePage("user2");

    await waitFor(() => {
      expect(getUserProfileApiMock).toHaveBeenCalledWith("user2");
      expect(getUserProfileApiMock).toHaveBeenCalledTimes(2);
    });
  });

  it("should show FollowButton when logged in user views another user's profile", async () => {
    vi.mocked(userService.getUserProfileApi).mockResolvedValueOnce(mockProfile);

    const loggedInUser: TestUser = {
      id: 1,
      username: "loggeduser",
      email: "logged@example.com",
      following_count: 0,
      follower_count: 0,
    };

    renderProfilePage("testuser", loggedInUser);

    await waitFor(() => {
      expect(screen.getByTestId("follow-button")).toBeInTheDocument();
    });
  });

  it("should not show FollowButton when viewing own profile", async () => {
    const ownProfile = { ...mockProfile, username: "loggeduser" };
    vi.mocked(userService.getUserProfileApi).mockResolvedValueOnce(ownProfile);

    const loggedInUser: TestUser = {
      id: 1,
      username: "loggeduser",
      email: "logged@example.com",
      following_count: 0,
      follower_count: 0,
    };

    renderProfilePage("loggeduser", loggedInUser);

    await waitFor(() => {
      expect(screen.queryByTestId("follow-button")).not.toBeInTheDocument();
    });
  });

  it("should not show FollowButton when not logged in", async () => {
    vi.mocked(userService.getUserProfileApi).mockResolvedValueOnce(mockProfile);

    renderProfilePage("testuser", null);

    await waitFor(() => {
      expect(screen.queryByTestId("follow-button")).not.toBeInTheDocument();
    });
  });

  it("should update profile when FollowButton is clicked", async () => {
    const getUserProfileApiMock = vi.mocked(userService.getUserProfileApi);
    const initialProfile = { ...mockProfile, is_following: false };
    const updatedProfile = { ...mockProfile, is_following: true };

    getUserProfileApiMock
      .mockResolvedValueOnce(initialProfile)
      .mockResolvedValueOnce(updatedProfile);

    const loggedInUser: TestUser = {
      id: 1,
      username: "loggeduser",
      email: "logged@example.com",
      following_count: 0,
      follower_count: 0,
    };

    renderProfilePage("testuser", loggedInUser);

    await waitFor(() => {
      expect(screen.getByTestId("follow-button")).toBeInTheDocument();
    });

    // Simulate follow button click
    screen.getByTestId("follow-button").click();

    await waitFor(() => {
      expect(getUserProfileApiMock).toHaveBeenCalledTimes(2);
    });
  });

  it("should show loading state initially", () => {
    vi.mocked(userService.getUserProfileApi).mockImplementation(
      () => new Promise(() => {}) // Never resolving promise to keep loading state
    );

    renderProfilePage();

    expect(screen.queryByText(mockProfile.username)).not.toBeInTheDocument();
    expect(screen.queryByTestId("post-list")).not.toBeInTheDocument();
  });
});
