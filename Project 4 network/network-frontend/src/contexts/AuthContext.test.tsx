import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "./AuthContext";

describe("AuthContext", () => {
  it("provides user state and setUser function", async () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>,
    });

    await act(async () => {
      // Wait for any pending state updates
    });

    expect(result.current.user).toBe(null);
    expect(typeof result.current.setUser).toBe("function");
  });

  it("updates user state when setUser is called", async () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>,
    });

    await act(async () => {
      // Wait for any pending state updates
    });

    const testUser = {
      id: 1,
      username: "testuser",
      email: "test@example.com",
      following_count: 0,
      follower_count: 0,
    };

    act(() => {
      result.current.setUser(testUser);
    });

    expect(result.current.user).toEqual(testUser);
  });

  it("throws error when useAuth is used outside of AuthProvider", () => {
    const consoleError = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});

    expect(() => {
      renderHook(() => useAuth());
    }).toThrow("useAuth must be used within an AuthProvider");

    consoleError.mockRestore();
  });
});
