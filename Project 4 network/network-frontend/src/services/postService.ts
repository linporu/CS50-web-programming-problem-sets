import { fetchWithConfig } from "./api";

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
  };
}

export const getPostApi = async () => {
  return fetchWithConfig("/api/posts", {
    method: "GET",
  });
};
