import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "../src/contexts/AuthContext";

describe("AuthContext", () => {
  it("provides user state and setUser function", () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    expect(result.current.user).toBe(null);
    expect(typeof result.current.setUser).toBe("function");
  });

  it("updates user state when setUser is called", () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    const testUser = { username: "testuser", email: "test@example.com" };

    act(() => {
      result.current.setUser(testUser);
    });

    expect(result.current.user).toEqual(testUser);
  });

  it("throws error when useAuth is used outside of AuthProvider", () => {
    expect(() => {
      renderHook(() => useAuth());
    }).toThrow("useAuth must be used within an AuthProvider");
  });
});
