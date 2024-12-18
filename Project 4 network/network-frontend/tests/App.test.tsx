import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "../src/App";

describe("App Component Tests", () => {
  it("should render the main layout with routes", () => {
    render(<App />);

    // Check if homepage is rendered correctly
    expect(screen.getByRole("main")).toBeInTheDocument();
  });

  it("should render navigation links", () => {
    render(<App />);

    // Check if navigation links exist
    expect(screen.getByRole("link", { name: /login/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /register/i })).toBeInTheDocument();
  });
});
