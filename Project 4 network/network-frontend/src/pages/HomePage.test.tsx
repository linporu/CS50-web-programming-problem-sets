import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import HomePage from "./HomePage";
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

const renderHomePage = async () => {
  render(
    <AuthProvider>
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    </AuthProvider>
  );

  // Wait for loading state to finish
  await waitFor(() => {
    expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
  });
};

describe("HomePage", () => {
  it("renders the homepage title correctly", async () => {
    await renderHomePage();
    expect(screen.getByText("All Posts")).toBeInTheDocument();
  });

  it("renders with correct container styling", async () => {
    const { container } = render(
      <AuthProvider>
        <BrowserRouter>
          <HomePage />
        </BrowserRouter>
      </AuthProvider>
    );
    await waitFor(() => {
      expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
    });
    const mainContainer = container.firstChild as HTMLElement;
    expect(mainContainer).toHaveClass("container", "mx-auto", "px-4", "py-8");
  });

  it("renders the PostList component", async () => {
    await renderHomePage();
    expect(screen.getByTestId("mock-post-list")).toBeInTheDocument();
  });

  it("renders heading with correct styling", async () => {
    await renderHomePage();
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading).toHaveClass("text-2xl", "font-bold", "mb-6");
  });
});
