import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import FollowingPage from "./FollowingPage";
import { AuthProvider } from "../contexts/AuthContext";
import { BrowserRouter } from "react-router-dom";

// Mock the PostList component
vi.mock("../components/Posts/PostList", () => ({
  default: () => <div data-testid="mock-post-list">PostList Mock</div>,
}));

// Mock auth service
vi.mock("../services/authService", () => ({
  checkAuthStatus: vi.fn().mockResolvedValue({ user: null }),
}));

const renderFollowingPage = async () => {
  render(
    <AuthProvider>
      <BrowserRouter>
        <FollowingPage />
      </BrowserRouter>
    </AuthProvider>
  );

  // Wait for loading state to finish
  await waitFor(() => {
    expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
  });
};

describe("FollowingPage", () => {
  it("renders the following page title correctly", async () => {
    await renderFollowingPage();
    expect(screen.getByText("Following Posts")).toBeInTheDocument();
  });

  it("renders with correct container styling", async () => {
    const { container } = render(
      <AuthProvider>
        <BrowserRouter>
          <FollowingPage />
        </BrowserRouter>
      </AuthProvider>
    );
    await waitFor(() => {
      expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
    });
    const mainContainer = container.firstChild as HTMLElement;
    expect(mainContainer).toHaveClass("container", "mx-auto", "px-4");
  });

  it("renders the PostList component with following mode", async () => {
    await renderFollowingPage();
    const postList = screen.getByTestId("mock-post-list");
    expect(postList).toBeInTheDocument();
  });

  it("renders heading with correct styling", async () => {
    await renderFollowingPage();
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading).toHaveClass("text-2xl", "font-bold", "mb-4");
  });
});
