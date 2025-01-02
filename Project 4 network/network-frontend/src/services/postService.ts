import { fetchWithConfig } from "./api";

interface PostApiResponse {
  message: string;
  posts: GetPostResponse[];
}

export interface GetPostResponse {
  id: number;
  content: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
  likes_count: number;
  comments_count: number;
  comments: {
    id: number;
    content: string;
    created_by: string;
    created_at: string;
    is_deleted: boolean;
  }[];
}

export const getPostApi = async (): Promise<GetPostResponse[]> => {
  const response = (await fetchWithConfig("/api/posts", {
    method: "GET",
  })) as PostApiResponse;
  console.log(response.message);
  return response.posts;
};

export const getFollowingPostApi = async (): Promise<GetPostResponse[]> => {
  const response = (await fetchWithConfig("/api/posts/following", {
    method: "GET",
  })) as PostApiResponse;
  console.log(response.message);
  return response.posts;
};

interface CreatePostResponse {
  message: string;
  error?: string;
}

export const createPostApi = async (
  content: string
): Promise<CreatePostResponse> => {
  const requestBody = {
    content: content,
  };

  const response = (await fetchWithConfig("/api/posts", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestBody),
  })) as CreatePostResponse;

  if (response.error) {
    throw new Error(response.error);
  }

  return response;
};

interface EditPostResponse {
  message: string;
  error?: string;
}

export const editPostApi = async (
  post_id: number,
  content: string
): Promise<EditPostResponse> => {
  const requestBody = {
    content: content,
  };

  const response = (await fetchWithConfig(`/api/posts/${post_id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestBody),
  })) as EditPostResponse;

  if (response.error) {
    throw new Error(response.error);
  }

  return response;
};
