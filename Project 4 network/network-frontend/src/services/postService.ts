import { fetchWithConfig } from "./api";

// API Response Types
interface SuccessResponse {
  message: string;
}

interface ErrorResponse {
  error: string;
}

// Discriminated union type for API responses
type ApiResponse<T> = (T & SuccessResponse) | ErrorResponse;

// Post related data structures
export interface Post {
  id: number;
  content: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
  likes_count: number;
  comments_count: number;
  is_liked: boolean;
  comments: {
    id: number;
    content: string;
    created_by: string;
    created_at: string;
    is_deleted: boolean;
  }[];
}

interface PostList {
  posts: Post[];
}

// Shared error handling function
const handleApiResponse = <T>(response: ApiResponse<T>): T => {
  if ("error" in response) {
    throw new Error(response.error);
  }
  return response;
};

// Shared function to handle posts array response
const handlePostsResponse = (response: unknown): Post[] => {
  if (Array.isArray(response)) {
    return response;
  }

  if (response && typeof response === "object" && "posts" in response) {
    return (response as PostList).posts;
  }

  throw new Error("Invalid response format");
};

export const getAllPostsApi = async (): Promise<Post[]> => {
  const response = await fetchWithConfig("/api/posts", {
    method: "GET",
  });
  return handlePostsResponse(response);
};

export const getPostApi = async (post_id: number): Promise<Post> => {
  const response = (await fetchWithConfig(`/api/posts/${post_id}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })) as ApiResponse<Post>;
  return handleApiResponse(response);
};

export const getFollowingPostApi = async (): Promise<Post[]> => {
  const response = await fetchWithConfig("/api/posts/following", {
    method: "GET",
  });
  return handlePostsResponse(response);
};

export const createPostApi = async (
  content: string
): Promise<SuccessResponse> => {
  const response = (await fetchWithConfig("/api/posts", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ content }),
  })) as ApiResponse<SuccessResponse>;
  return handleApiResponse(response);
};

export const editPostApi = async (
  post_id: number,
  content: string
): Promise<SuccessResponse> => {
  const response = (await fetchWithConfig(`/api/posts/${post_id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ content }),
  })) as ApiResponse<SuccessResponse>;
  return handleApiResponse(response);
};

export const deletePostApi = async (
  post_id: number
): Promise<SuccessResponse> => {
  const response = (await fetchWithConfig(`/api/posts/${post_id}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
  })) as ApiResponse<SuccessResponse>;
  return handleApiResponse(response);
};

export const likePostApi = async (
  post_id: number
): Promise<SuccessResponse> => {
  const response = (await fetchWithConfig(`/api/posts/${post_id}/like`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })) as ApiResponse<SuccessResponse>;
  return handleApiResponse(response);
};

export const unLikePostApi = async (
  post_id: number
): Promise<SuccessResponse> => {
  const response = (await fetchWithConfig(`/api/posts/${post_id}/like`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
  })) as ApiResponse<SuccessResponse>;
  return handleApiResponse(response);
};
