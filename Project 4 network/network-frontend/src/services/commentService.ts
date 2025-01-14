import { fetchWithConfig } from "./api";

// Comment Type
export interface Comment {
  id: number;
  content: string;
  created_by: string;
  created_at: string;
  is_deleted: boolean;
}

// API Response Types
interface SuccessResponse {
  message: string;
}

interface ErrorResponse {
  error: string;
}

// Discriminated union type for API responses
type ApiResponse<T> = (T & SuccessResponse) | ErrorResponse;

// Shared error handling function
const handleApiResponse = <T>(response: ApiResponse<T>): T => {
  if ("error" in response) {
    throw new Error(response.error);
  }
  return response;
};

export const createCommentApi = async (
  post_id: number,
  content: string,
  onSuccess?: () => void
): Promise<SuccessResponse> => {
  const response = (await fetchWithConfig(`/api/posts/${post_id}/comments`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ content }),
  })) as ApiResponse<SuccessResponse>;
  const result = handleApiResponse(response);
  onSuccess?.();
  return result;
};

export const editCommentApi = async (
  comment_id: number,
  content: string,
  onSuccess?: () => void
): Promise<SuccessResponse> => {
  const response = (await fetchWithConfig(`/api/comment/${comment_id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ content }),
  })) as ApiResponse<SuccessResponse>;
  const result = handleApiResponse(response);
  onSuccess?.();
  return result;
};

export const deleteCommentApi = async (
  comment_id: number,
  onSuccess?: () => void
): Promise<SuccessResponse> => {
  const response = (await fetchWithConfig(`/api/comment/${comment_id}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
  })) as ApiResponse<SuccessResponse>;
  const result = handleApiResponse(response);
  onSuccess?.();
  return result;
};

// Get comments for a specific post
export const getCommentsApi = async (post_id: number): Promise<Comment[]> => {
  const response = (await fetchWithConfig(`/api/posts/${post_id}/comments`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })) as ApiResponse<{ comments: Comment[] }>;

  const result = handleApiResponse(response);
  return result.comments;
};
