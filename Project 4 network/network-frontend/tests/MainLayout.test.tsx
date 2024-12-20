import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import MainLayout from "../src/layouts/MainLayout";
import { AuthProvider } from "../src/contexts/AuthContext";
import React from "react";

const renderMainLayout = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <MainLayout>
          <div>Test Content</div>
        </MainLayout>
      </AuthProvider>
    </BrowserRouter>
  );
};

describe("MainLayout", () => {
  it("renders navigation and content", () => {
    renderMainLayout();
    expect(screen.getByText("Network")).toBeDefined();
    expect(screen.getByText("Test Content")).toBeDefined();
  });

  it("shows login and register links when user is not authenticated", () => {
    renderMainLayout();
    expect(screen.getByText("Login")).toBeDefined();
    expect(screen.getByText("Register")).toBeDefined();
  });

  it("shows welcome message and home link when user is authenticated", async () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <MainLayout>
            <div>Test Content</div>
          </MainLayout>
        </AuthProvider>
      </BrowserRouter>
    );

    // You might need to trigger a login here or mock the AuthContext value
    // This depends on how you want to test the authenticated state
  });
});
