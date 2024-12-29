import {
  describe,
  it,
  expect,
  beforeAll,
  afterAll,
  afterEach,
  vi,
} from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { getPostApi } from "./postService";
import { API_BASE_URL } from "./api";

// Declare fetch as a global type
declare global {
  interface Window {
    fetch: typeof fetch;
  }
}

// Mock API response data
const mockApiResponse = {
  message: "Posts retrieved successfully",
  posts: [
    {
      id: 1,
      content: "Test post",
      created_by: "testuser",
      created_at: "2024-03-20T10:00:00Z",
      updated_at: "2024-03-20T10:00:00Z",
      is_deleted: false,
      likes_count: 0,
      comments_count: 0,
      comments: [
        {
          id: 1,
          content: "Test comment",
          created_by: "commentuser",
          created_at: "2024-03-20T10:01:00Z",
          is_deleted: false,
        },
      ],
    },
  ],
};

// Setup MSW server
const server = setupServer(
  // Mock CSRF endpoint with full URL
  http.get(`${API_BASE_URL}/csrf`, () => {
    return new HttpResponse(null, {
      status: 200,
      headers: {
        "X-CSRFToken": "fake-csrf-token",
      },
    });
  }),

  // Mock posts endpoint with full URL
  http.get(`${API_BASE_URL}/api/posts`, () => {
    return new HttpResponse(JSON.stringify(mockApiResponse), {
      status: 200,
      headers: {
        "content-type": "application/json",
      },
    });
  })
);

// Mock fetch for Node environment
vi.stubGlobal("fetch", vi.fn());

beforeAll(() => {
  // Mock document.cookie for CSRF token
  Object.defineProperty(document, "cookie", {
    writable: true,
    value: "csrftoken=fake-csrf-token",
  });

  server.listen();
});

// Reset handlers and mocks after each test
afterEach(() => {
  server.resetHandlers();
  vi.clearAllMocks();
});

// Close server after all tests
afterAll(() => {
  server.close();
  vi.restoreAllMocks();
});

describe("postService", () => {
  describe("getPostApi", () => {
    it("should successfully fetch posts list", async () => {
      server.use(
        http.get(`${API_BASE_URL}/api/posts`, () => {
          return new HttpResponse(JSON.stringify(mockApiResponse), {
            status: 200,
            headers: {
              "content-type": "application/json",
            },
          });
        })
      );

      const response = await getPostApi();
      expect(response).toEqual(mockApiResponse.posts);
    });

    it("should throw error when API fails", async () => {
      // Mock API error with full URL
      server.use(
        http.get(`${API_BASE_URL}/api/posts`, () => {
          return new HttpResponse(
            JSON.stringify({ error: "Internal Server Error" }),
            {
              status: 500,
              headers: {
                "content-type": "application/json",
              },
            }
          );
        })
      );

      await expect(getPostApi()).rejects.toThrow("Internal Server Error");
    });
  });
});
