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

  it("should render navigation links", async () => {
    render(<App />);
    // Wait for loading to finish and find links
    await screen.findByRole("link", { name: /login/i });

    expect(screen.getByRole("link", { name: /login/i })).toBeDefined();
    expect(screen.getByRole("link", { name: /register/i })).toBeDefined();
  });
});
