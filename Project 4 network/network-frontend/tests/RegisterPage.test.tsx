import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import RegisterPage from "../src/pages/RegisterPage";
import * as authService from "../src/services/authService";
import userEvent from "@testing-library/user-event";
import React from "react";

// Mock the entire authService module
vi.mock("../src/services/authService");
// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("RegisterPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderRegisterPage = () => {
    return render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    );
  };

  // Helper function to fill form
  const fillForm = async (
    username = "testuser",
    email = "test@example.com",
    password = "password123",
    confirmation = "password123"
  ) => {
    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/username/i), username);
    await user.type(screen.getByLabelText(/email/i), email);
    await user.type(screen.getByLabelText(/^password/i), password);
    await user.type(screen.getByLabelText(/confirm password/i), confirmation);
  };

  it("renders all form elements correctly", () => {
    renderRegisterPage();

    expect(
      screen.getByRole("heading", { name: /register/i })
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /register/i })
    ).toBeInTheDocument();
  });

  it("shows error when form is submitted with empty fields", async () => {
    renderRegisterPage();

    fireEvent.click(screen.getByRole("button", { name: /register/i }));

    expect(
      await screen.findByText("Please fill in all fields")
    ).toBeInTheDocument();
  });

  it("shows error when email is invalid", async () => {
    renderRegisterPage();

    await fillForm("testuser", "invalid-email");

    const form = screen.getByRole("form");
    fireEvent.submit(form);

    expect(
      await screen.findByText("Please enter a valid email address")
    ).toBeInTheDocument();
  });

  it("shows error when passwords do not match", async () => {
    renderRegisterPage();

    await fillForm("testuser", "test@example.com", "password123", "different");

    fireEvent.click(screen.getByRole("button", { name: /register/i }));

    expect(await screen.findByText("Passwords must match")).toBeInTheDocument();
  });

  it("navigates to login page on successful registration", async () => {
    vi.mocked(authService.registerApi).mockResolvedValueOnce({
        message: "Registration successful",
        user: {
            id: 0,
            username: "",
            email: "",
            following_count: 0,
            follower_count: 0
        }
    });

    renderRegisterPage();

    await fillForm();

    fireEvent.click(screen.getByRole("button", { name: /register/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/login", {
        state: {
          message:
            "Registration successful! Please login with your credentials.",
        },
      });
    });
  });

  it("shows error message when registration fails", async () => {
    const errorMessage = "Registration failed";
    vi.mocked(authService.registerApi).mockRejectedValueOnce(
      new Error(errorMessage)
    );

    renderRegisterPage();

    await fillForm();

    fireEvent.click(screen.getByRole("button", { name: /register/i }));

    expect(await screen.findByText(errorMessage)).toBeInTheDocument();
  });

  it("updates form fields when typing", async () => {
    renderRegisterPage();

    const testValues = {
      username: "testuser",
      email: "test@example.com",
      password: "password123",
      confirmation: "password123",
    };

    await fillForm(
      testValues.username,
      testValues.email,
      testValues.password,
      testValues.confirmation
    );

    expect(screen.getByLabelText(/username/i)).toHaveValue(testValues.username);
    expect(screen.getByLabelText(/email/i)).toHaveValue(testValues.email);
    expect(screen.getByLabelText(/^password/i)).toHaveValue(
      testValues.password
    );
    expect(screen.getByLabelText(/confirm password/i)).toHaveValue(
      testValues.confirmation
    );
  });
});
