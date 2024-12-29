import { describe, it, expect, beforeEach, vi } from "vitest";
import { fetchWithConfig, API_BASE_URL } from "../src/services/api";

describe("API Service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset document.cookie before each test
    Object.defineProperty(document, "cookie", {
      writable: true,
      value: "",
    });
    // Reset CSRF token initialization state
    // @ts-expect-error Accessing private variable for testing purposes
    global.csrfTokenInitialized = false;
  });

  it("makes request with correct configuration", async () => {
    const mockResponse = { data: "test" };
    const mockFetch = vi.fn(() =>
      Promise.resolve(
        new Response(JSON.stringify(mockResponse), {
          status: 200,
          headers: new Headers({
            "content-type": "application/json",
          }),
        })
      )
    );

    vi.stubGlobal("fetch", mockFetch);

    const endpoint = "/test";
    const options: RequestInit = {
      method: "POST",
      body: JSON.stringify({ test: true }),
    };

    await fetchWithConfig(endpoint, options);

    expect(fetch).toHaveBeenCalledWith(`${API_BASE_URL}${endpoint}`, {
      method: options.method,
      body: options.body,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": "",
        ...(options.headers || {}),
      },
    });
  });

  it("throws error when response is not ok", async () => {
    const mockFetch = vi.fn(() =>
      Promise.resolve(
        new Response(JSON.stringify({ error: "Test error" }), {
          status: 400,
          headers: new Headers({
            "content-type": "application/json",
          }),
        })
      )
    );

    vi.stubGlobal("fetch", mockFetch);

    await expect(fetchWithConfig("/test")).rejects.toThrow("Test error");
  });

  it("returns null for non-JSON successful responses", async () => {
    const mockFetch = vi.fn(() =>
      Promise.resolve(
        new Response("<html></html>", {
          status: 200,
          headers: new Headers({
            "content-type": "text/html",
          }),
        })
      )
    );

    vi.stubGlobal("fetch", mockFetch);

    const result = await fetchWithConfig("/test");
    expect(result).toBeNull();
  });

  it("returns null for non-JSON error responses", async () => {
    const mockFetch = vi.fn(() =>
      Promise.resolve(
        new Response("<error>404</error>", {
          status: 404,
          headers: new Headers({
            "content-type": "text/html",
          }),
        })
      )
    );

    vi.stubGlobal("fetch", mockFetch);
    const response = await fetchWithConfig("/test");
    expect(response).toBeNull();
  });

  it("initializes CSRF token when not present", async () => {
    // @ts-expect-error Accessing private variable for testing purposes
    global.csrfTokenInitialized = false;

    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(null, {
          status: 200,
          headers: new Headers(),
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ data: "test" }), {
          status: 200,
          headers: new Headers({
            "content-type": "application/json",
          }),
        })
      );

    vi.stubGlobal("fetch", mockFetch);
    await fetchWithConfig("/test");

    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(mockFetch.mock.calls[0][0]).toBe(`${API_BASE_URL}/csrf`);
  });

  it("uses existing CSRF token without initialization", async () => {
    document.cookie = "csrftoken=test-token";

    const mockFetch = vi.fn().mockResolvedValueOnce(
      new Response(JSON.stringify({ data: "test" }), {
        status: 200,
        headers: new Headers({
          "content-type": "application/json",
        }),
      })
    );

    vi.stubGlobal("fetch", mockFetch);
    await fetchWithConfig("/test");

    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch.mock.calls[0][1].headers["X-CSRFToken"]).toBe(
      "test-token"
    );
  });

  it("handles JSON parsing errors", async () => {
    const mockFetch = vi.fn(() =>
      Promise.resolve(
        new Response("invalid json", {
          status: 200,
          headers: new Headers({
            "content-type": "application/json",
          }),
        })
      )
    );

    vi.stubGlobal("fetch", mockFetch);
    await expect(fetchWithConfig("/test")).rejects.toThrow(
      "Invalid response format from server"
    );
  });

  it("normalizes endpoint with leading slash", async () => {
    const mockFetch = vi.fn(() =>
      Promise.resolve(
        new Response(JSON.stringify({ data: "test" }), {
          status: 200,
          headers: new Headers({
            "content-type": "application/json",
          }),
        })
      )
    );

    vi.stubGlobal("fetch", mockFetch);
    await fetchWithConfig("test"); // Note: no leading slash

    expect(mockFetch).toHaveBeenCalledWith(
      `${API_BASE_URL}/test`,
      expect.any(Object)
    );
  });

  it("preserves custom headers while adding default headers", async () => {
    document.cookie = "csrftoken=test-token";
    const customHeaders = {
      "Custom-Header": "custom-value",
    };

    const mockFetch = vi.fn().mockResolvedValueOnce(
      new Response(JSON.stringify({ data: "test" }), {
        status: 200,
        headers: new Headers({
          "content-type": "application/json",
        }),
      })
    );

    vi.stubGlobal("fetch", mockFetch);

    await fetchWithConfig("/test", {
      headers: customHeaders,
    });

    expect(mockFetch).toHaveBeenCalledWith(
      `${API_BASE_URL}/test`,
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          "X-CSRFToken": "test-token",
          "Custom-Header": "custom-value",
        }),
      })
    );
  });

  it("handles CSRF token initialization failure", async () => {
    const mockFetch = vi
      .fn()
      .mockRejectedValueOnce(new Error("CSRF initialization failed"));

    vi.stubGlobal("fetch", mockFetch);

    await expect(fetchWithConfig("/test")).rejects.toThrow(
      "CSRF initialization failed"
    );
  });

  it("handles non-JSON success response with no content-type", async () => {
    const mockFetch = vi.fn(() =>
      Promise.resolve(
        new Response(null, {
          status: 200,
          headers: new Headers(),
        })
      )
    );

    vi.stubGlobal("fetch", mockFetch);
    const result = await fetchWithConfig("/test");
    expect(result).toBeNull();
  });

  it("successfully fetches and returns posts data", async () => {
    // Mock response data
    const mockPostsResponse = {
      message: "Get posts successfully.",
      posts: [
        {
          id: 1,
          content: "test",
          created_by: "test",
          created_at: "2024-12-29 14:48:11",
          updated_at: "2024-12-29 14:48:11",
          is_deleted: false,
          likes_count: 0,
          comments: [],
          comments_count: 0,
        },
      ],
    };

    // Create mock fetch function
    const mockFetch = vi.fn(() =>
      Promise.resolve(
        new Response(JSON.stringify(mockPostsResponse), {
          status: 200,
          headers: new Headers({
            "content-type": "application/json",
          }),
        })
      )
    );

    // Replace global fetch with mock
    vi.stubGlobal("fetch", mockFetch);

    // Call the API
    const result = await fetchWithConfig("/posts");

    // Verify the response
    expect(result).toEqual(mockPostsResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      `${API_BASE_URL}/posts`,
      expect.objectContaining({
        credentials: "include",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      })
    );
  });
});
