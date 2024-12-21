import { describe, it, expect, beforeEach, vi } from "vitest";
import { fetchWithConfig, API_BASE_URL } from "../src/services/api";

describe("API Service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("makes request with correct configuration", async () => {
    const mockResponse = { data: "test" };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
        headers: {
          get: (header: string) =>
            header === "content-type" ? "application/json" : null,
        },
      })
    );

    const endpoint = "/test";
    const options = {
      method: "POST",
      body: JSON.stringify({ test: true }),
    };

    await fetchWithConfig(endpoint, options);

    expect(fetch).toHaveBeenCalledWith(`${API_BASE_URL}${endpoint}`, {
      ...options,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    });
  });

  it("throws error when response is not ok", async () => {
    const errorMessage = "Test error";
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ error: errorMessage }),
        headers: {
          get: (header: string) =>
            header === "content-type" ? "application/json" : null,
        },
      })
    );

    await expect(fetchWithConfig("/test")).rejects.toThrow(errorMessage);
  });

  it("returns null for non-JSON successful responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        headers: {
          get: () => "text/html",
        },
      })
    );

    const result = await fetchWithConfig("/test");
    expect(result).toBeNull();
  });

  it("throws generic error for non-JSON error responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: false,
        headers: {
          get: () => "text/html",
        },
      })
    );

    await expect(fetchWithConfig("/test")).rejects.toThrow(
      "Network response was not ok"
    );
  });
});
