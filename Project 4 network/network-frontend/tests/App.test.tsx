import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "../src/App";
import React from "react";

describe("App Component Tests", () => {
  it("should render the main layout with routes", () => {
    render(<App />);
    // Check if homepage is rendered correctly
    expect(screen.getByRole("main")).toBeDefined();
  });

  it("should render navigation links", () => {
    render(<App />);

    // Check if navigation links exist
    expect(screen.getByRole("link", { name: /login/i })).toBeDefined();
    expect(screen.getByRole("link", { name: /register/i })).toBeDefined();
  });
});
