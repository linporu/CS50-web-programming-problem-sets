import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ProfilePage from "./ProfilePage";
import * as userService from "../services/userService";

// Mock the userService
vi.mock("../services/userService");
// Mock the PostList component
vi.mock("../components/Posts/PostList", () => ({
  default: () => <div data-testid="post-list">PostList Component</div>,
}));

const mockProfile = {
  username: "testuser",
  email: "test@example.com",
  following_count: 10,
  follower_count: 20,
};

describe("ProfilePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderProfilePage = (username: string = "testuser") => {
    return render(
      <MemoryRouter initialEntries={[`/profile/${username}`]}>
        <Routes>
          <Route path="/profile/:username" element={<ProfilePage />} />
        </Routes>
      </MemoryRouter>
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
    render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>
    );

    expect(screen.queryByTestId("post-list")).not.toBeInTheDocument();
  });

  it("should fetch new profile when username changes", async () => {
    const getUserProfileApiMock = vi.mocked(userService.getUserProfileApi);

    // 設定兩個不同的 profile 資料
    const user1Profile = { ...mockProfile, username: "user1" };
    const user2Profile = { ...mockProfile, username: "user2" };

    // 設定 mock 回應
    getUserProfileApiMock
      .mockResolvedValueOnce(user1Profile)
      .mockResolvedValueOnce(user2Profile);

    const { unmount } = renderProfilePage("user1");

    // 驗證第一次呼叫
    await waitFor(() => {
      expect(getUserProfileApiMock).toHaveBeenCalledWith("user1");
    });

    // 卸載第一個實例
    unmount();

    // 重新渲染新的 username
    renderProfilePage("user2");

    // 驗證第二次呼叫
    await waitFor(() => {
      expect(getUserProfileApiMock).toHaveBeenCalledWith("user2");
      expect(getUserProfileApiMock).toHaveBeenCalledTimes(2);
    });
  });
});
