import { describe, it, expect, beforeAll, afterAll, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import PostList from "../src/components/Posts/PostList";

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
  })
);

// Setup and teardown
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("PostList Component", () => {
  it("shows loading state initially", () => {
    render(<PostList />);
    expect(screen.getByText("Loading posts...")).toBeInTheDocument();
  });

  it("renders posts successfully", async () => {
    render(<PostList />);

    // Wait for loading to finish and content to appear
    await waitFor(() => {
      expect(screen.queryByText("Loading posts...")).not.toBeInTheDocument();
    });

    // Check if post content is rendered
    expect(screen.getByText("Test post 1")).toBeInTheDocument();
  });

  it("shows error message when API call fails", async () => {
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

    render(<PostList />);
    await waitFor(() => {
      expect(screen.getByText("An error occurred")).toBeInTheDocument();
    });
  });

  it('shows "No posts yet" when API returns empty array', async () => {
    server.use(
      http.get("http://localhost:8000/api/posts", () => {
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

    render(<PostList />);
    await waitFor(() => {
      expect(screen.getByText("No posts yet.")).toBeInTheDocument();
    });
  });
});
