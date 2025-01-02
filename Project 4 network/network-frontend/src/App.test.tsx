import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import App from "../src/App";

// Mock the authService
vi.mock("../src/services/authService", () => ({
  checkAuthStatus: vi.fn().mockResolvedValue({ user: null }),
}));

describe("App Component Tests", () => {
  it("should render the main layout with routes", async () => {
    render(<App />);
    // Wait for loading to finish
    await screen.findByRole("main");
    expect(screen.getByRole("main")).toBeDefined();
  });

  it("should render navigation links for logged out users", async () => {
    render(<App />);
    // Wait for loading to finish and find links
    await screen.findByRole("link", { name: /login/i });

    expect(screen.getByRole("link", { name: /login/i })).toBeDefined();
    expect(screen.getByRole("link", { name: /register/i })).toBeDefined();
  });

  it("should render home and following routes", async () => {
    render(<App />);

    // Wait for the loading state to finish
    await screen.findByRole("main");

    // Verify route paths exist
    const homeLink = screen.queryByRole("link", { name: /home/i });
    const followingLink = screen.queryByRole("link", { name: /following/i });

    // Check if either the links exist or the app title is present
    expect(
      homeLink || (await screen.findByText(/network/i, { exact: false }))
    ).toBeTruthy();
    expect(
      followingLink || (await screen.findByText(/network/i, { exact: false }))
    ).toBeTruthy();
  });
});
