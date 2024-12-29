import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import HomePage from "../src/pages/HomePage";

// Mock the PostList component
vi.mock("../src/components/Posts/PostList", () => ({
  default: () => <div data-testid="mock-post-list">PostList Mock</div>,
}));

describe("HomePage", () => {
  it("renders the homepage title correctly", () => {
    render(<HomePage />);
    expect(screen.getByText("All Posts")).toBeInTheDocument();
  });

  it("renders with correct container styling", () => {
    const { container } = render(<HomePage />);
    const mainContainer = container.firstChild as HTMLElement;
    expect(mainContainer).toHaveClass("container", "mx-auto", "px-4", "py-8");
  });

  it("renders the PostList component", () => {
    render(<HomePage />);
    expect(screen.getByTestId("mock-post-list")).toBeInTheDocument();
  });

  it("renders heading with correct styling", () => {
    render(<HomePage />);
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading).toHaveClass("text-2xl", "font-bold", "mb-6");
  });
});
