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
import {
  getAllPostsApi,
  createPostApi,
  editPostApi,
  getFollowingPostApi,
  deletePostApi,
} from "./postService";
import { API_BASE_URL } from "./api";

// Declare fetch as a global type
declare global {
  interface Window {
    fetch: typeof fetch;
  }
}

// Mock API response data
const mockGetPostsResponse = {
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

const mockGetFollowingPostsResponse = {
  message: "Following posts retrieved successfully",
  posts: [
    {
      id: 2,
      content: "Following test post",
      created_by: "followeduser",
      created_at: "2024-03-20T10:00:00Z",
      updated_at: "2024-03-20T10:00:00Z",
      is_deleted: false,
      likes_count: 0,
      comments_count: 0,
      comments: [],
    },
  ],
};

const mockCreatePostResponse = {
  message: "Post created successfully",
};

const mockEditPostResponse = {
  message: "Post updated successfully",
};

const mockDeletePostResponse = {
  message: "Post deleted successfully",
};

// Setup MSW server
const server = setupServer(
  // Mock CSRF endpoint
  http.get(`${API_BASE_URL}/csrf`, () => {
    return new HttpResponse(null, {
      status: 200,
      headers: {
        "X-CSRFToken": "fake-csrf-token",
      },
    });
  }),

  // Mock GET posts endpoint
  http.get(`${API_BASE_URL}/api/posts`, () => {
    return new HttpResponse(JSON.stringify(mockGetPostsResponse), {
      status: 200,
      headers: {
        "content-type": "application/json",
      },
    });
  }),

  // Mock GET following posts endpoint
  http.get(`${API_BASE_URL}/api/posts/following`, () => {
    return new HttpResponse(JSON.stringify(mockGetFollowingPostsResponse), {
      status: 200,
      headers: {
        "content-type": "application/json",
      },
    });
  }),

  // Mock POST posts endpoint
  http.post(`${API_BASE_URL}/api/posts`, () => {
    return new HttpResponse(JSON.stringify(mockCreatePostResponse), {
      status: 200,
      headers: {
        "content-type": "application/json",
      },
    });
  }),

  // Mock PATCH posts endpoint
  http.patch(`${API_BASE_URL}/api/posts/:id`, () => {
    return new HttpResponse(JSON.stringify(mockEditPostResponse), {
      status: 200,
      headers: {
        "content-type": "application/json",
      },
    });
  }),

  // Mock DELETE posts endpoint
  http.delete(`${API_BASE_URL}/api/posts/:id`, () => {
    return new HttpResponse(JSON.stringify(mockDeletePostResponse), {
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
  describe("getAllPostsApi", () => {
    it("should successfully fetch posts list", async () => {
      const response = await getAllPostsApi();
      expect(response).toEqual(mockGetPostsResponse.posts);
    });

    it("should handle array response format", async () => {
      server.use(
        http.get(`${API_BASE_URL}/api/posts`, () => {
          return new HttpResponse(
            JSON.stringify([
              {
                id: 1,
                content: "Test post",
                created_by: "testuser",
                created_at: "2024-03-20T10:00:00Z",
                updated_at: "2024-03-20T10:00:00Z",
                is_deleted: false,
                likes_count: 0,
                comments_count: 0,
                comments: [],
              },
            ]),
            {
              status: 200,
              headers: {
                "content-type": "application/json",
              },
            }
          );
        })
      );

      const response = await getAllPostsApi();
      expect(Array.isArray(response)).toBe(true);
      expect(response[0]).toHaveProperty("id", 1);
    });

    it("should throw error for invalid response format", async () => {
      server.use(
        http.get(`${API_BASE_URL}/api/posts`, () => {
          return new HttpResponse(
            JSON.stringify({ invalidKey: "invalid data" }),
            {
              status: 200,
              headers: {
                "content-type": "application/json",
              },
            }
          );
        })
      );

      await expect(getAllPostsApi()).rejects.toThrow("Invalid response format");
    });

    it("should throw error when API fails", async () => {
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

      await expect(getAllPostsApi()).rejects.toThrow("Internal Server Error");
    });
  });

  describe("createPostApi", () => {
    it("should successfully create a post", async () => {
      const content = "Test post content";
      const response = await createPostApi(content);
      expect(response).toEqual(mockCreatePostResponse);
    });

    it("should throw error when API fails", async () => {
      server.use(
        http.post(`${API_BASE_URL}/api/posts`, () => {
          return new HttpResponse(
            JSON.stringify({ error: "Failed to create post" }),
            {
              status: 400,
              headers: {
                "content-type": "application/json",
              },
            }
          );
        })
      );

      await expect(createPostApi("Test content")).rejects.toThrow(
        "Failed to create post"
      );
    });
  });

  describe("editPostApi", () => {
    it("should successfully edit a post", async () => {
      const postId = 1;
      const content = "Updated post content";
      const response = await editPostApi(postId, content);
      expect(response).toEqual(mockEditPostResponse);
    });

    it("should throw error when API fails", async () => {
      server.use(
        http.patch(`${API_BASE_URL}/api/posts/1`, () => {
          return new HttpResponse(
            JSON.stringify({ error: "Failed to update post" }),
            {
              status: 400,
              headers: {
                "content-type": "application/json",
              },
            }
          );
        })
      );

      await expect(editPostApi(1, "Updated content")).rejects.toThrow(
        "Failed to update post"
      );
    });
  });

  describe("getFollowingPostApi", () => {
    it("should successfully fetch following posts list", async () => {
      const response = await getFollowingPostApi();
      expect(response).toEqual(mockGetFollowingPostsResponse.posts);
    });

    it("should handle array response format", async () => {
      server.use(
        http.get(`${API_BASE_URL}/api/posts/following`, () => {
          return new HttpResponse(
            JSON.stringify([
              {
                id: 2,
                content: "Following test post",
                created_by: "followeduser",
                created_at: "2024-03-20T10:00:00Z",
                updated_at: "2024-03-20T10:00:00Z",
                is_deleted: false,
                likes_count: 0,
                comments_count: 0,
                comments: [],
              },
            ]),
            {
              status: 200,
              headers: {
                "content-type": "application/json",
              },
            }
          );
        })
      );

      const response = await getFollowingPostApi();
      expect(Array.isArray(response)).toBe(true);
      expect(response[0]).toHaveProperty("id", 2);
    });

    it("should throw error for invalid response format", async () => {
      server.use(
        http.get(`${API_BASE_URL}/api/posts/following`, () => {
          return new HttpResponse(
            JSON.stringify({ invalidKey: "invalid data" }),
            {
              status: 200,
              headers: {
                "content-type": "application/json",
              },
            }
          );
        })
      );

      await expect(getFollowingPostApi()).rejects.toThrow(
        "Invalid response format"
      );
    });

    it("should throw error when API fails", async () => {
      server.use(
        http.get(`${API_BASE_URL}/api/posts/following`, () => {
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

      await expect(getFollowingPostApi()).rejects.toThrow(
        "Internal Server Error"
      );
    });
  });

  describe("deletePostApi", () => {
    it("should successfully delete a post", async () => {
      const postId = 1;
      const response = await deletePostApi(postId);
      expect(response).toEqual(mockDeletePostResponse);
    });

    it("should throw error when API fails", async () => {
      server.use(
        http.delete(`${API_BASE_URL}/api/posts/1`, () => {
          return new HttpResponse(
            JSON.stringify({ error: "Failed to delete post" }),
            {
              status: 400,
              headers: {
                "content-type": "application/json",
              },
            }
          );
        })
      );

      await expect(deletePostApi(1)).rejects.toThrow("Failed to delete post");
    });
  });
});
