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
