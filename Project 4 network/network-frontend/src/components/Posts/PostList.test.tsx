import {
  describe,
  it,
  expect,
  beforeAll,
  afterAll,
  afterEach,
  vi,
} from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import PostList from "./PostList";
import { AuthContext } from "@/contexts/AuthContext";

// Mock data
const mockPosts = [
  {
    id: 1,
    content: "Test post 1",
    created_by: "user1",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    is_deleted: false,
    likes_count: 5,
    comments_count: 2,
    comments: [
      {
        id: 1,
        content: "Test comment",
        created_by: "user2",
        created_at: "2024-01-01T00:00:00Z",
        is_deleted: false,
      },
    ],
  },
];

const mockFollowingPosts = [
  {
    id: 2,
    content: "Following post 1",
    created_by: "followedUser",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    is_deleted: false,
    likes_count: 3,
    comments_count: 1,
    comments: [],
  },
];

// Setup MSW server
const server = setupServer(
  http.get("http://localhost:8000/csrf", () => {
    return new HttpResponse(null, {
      headers: {
        "Set-Cookie": "csrftoken=test-csrf-token",
      },
    });
  }),

  http.get("http://localhost:8000/api/posts", () => {
    return HttpResponse.json(
      {
        message: "Posts fetched successfully",
        posts: mockPosts,
      },
      {
        headers: {
          "Content-Type": "application/json",
        },
      }
    );
  }),

  http.get("http://localhost:8000/api/posts/following", () => {
    return HttpResponse.json(
      {
        message: "Following posts fetched successfully",
        posts: mockFollowingPosts,
      },
      {
        headers: {
          "Content-Type": "application/json",
        },
      }
    );
  })
);

// Setup and teardown
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("PostList Component", () => {
  const renderWithAuth = (component: React.ReactNode) => {
    return render(
      <AuthContext.Provider
        value={{
          user: null,
          setUser: vi.fn(),
          isAuthenticated: false,
          clearAuth: vi.fn(),
          _isDefault: false,
        }}
      >
        {component}
      </AuthContext.Provider>
    );
  };

  describe("All Posts Mode", () => {
    it("shows loading state initially", () => {
      renderWithAuth(<PostList mode="all" />);
      expect(screen.getByText("Loading posts...")).toBeInTheDocument();
    });

    it("renders posts successfully in all mode", async () => {
      renderWithAuth(<PostList mode="all" />);

      await waitFor(() => {
        expect(screen.queryByText("Loading posts...")).not.toBeInTheDocument();
      });

      expect(screen.getByText("Test post 1")).toBeInTheDocument();
      expect(screen.getByText("user1")).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText("What's on your mind?")
      ).toBeInTheDocument();
    });

    it("shows error message when API call fails in all mode", async () => {
      server.use(
        http.get("http://localhost:8000/api/posts", () => {
          return new HttpResponse(JSON.stringify({ message: "Server error" }), {
            status: 500,
            headers: {
              "Content-Type": "application/json",
            },
          });
        })
      );

      renderWithAuth(<PostList mode="all" />);
      await waitFor(() => {
        expect(screen.getByText("An error occurred")).toBeInTheDocument();
      });
    });
  });

  describe("Following Posts Mode", () => {
    it("renders following posts successfully", async () => {
      renderWithAuth(<PostList mode="following" />);

      await waitFor(() => {
        expect(screen.queryByText("Loading posts...")).not.toBeInTheDocument();
      });

      expect(screen.getByText("Following post 1")).toBeInTheDocument();
      expect(screen.getByText("followedUser")).toBeInTheDocument();
      expect(
        screen.queryByPlaceholderText("What's on your mind?")
      ).not.toBeInTheDocument();
    });

    it("shows error message when following API call fails", async () => {
      server.use(
        http.get("http://localhost:8000/api/posts/following", () => {
          return new HttpResponse(JSON.stringify({ message: "Server error" }), {
            status: 500,
            headers: {
              "Content-Type": "application/json",
            },
          });
        })
      );

      renderWithAuth(<PostList mode="following" />);
      await waitFor(() => {
        expect(screen.getByText("An error occurred")).toBeInTheDocument();
      });
    });

    it('shows "No posts yet" when following API returns empty array', async () => {
      server.use(
        http.get("http://localhost:8000/api/posts/following", () => {
          return HttpResponse.json(
            {
              message: "No posts found",
              posts: [],
            },
            {
              headers: {
                "Content-Type": "application/json",
              },
            }
          );
        })
      );

      renderWithAuth(<PostList mode="following" />);
      await waitFor(() => {
        expect(screen.getByText("No posts yet.")).toBeInTheDocument();
      });
    });
  });
});
