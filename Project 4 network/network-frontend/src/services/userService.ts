import { fetchWithConfig } from "./api";
import { GetPostResponse } from "./postService";

interface UserApiResponse {
  message: string;
  user: {
    username: string;
    email: string;
    following_count: number;
    follower_count: number;
  };
  posts: GetPostResponse[] | null;
}

export interface UserProfile {
  username: string;
  email: string;
  following_count: number;
  follower_count: number;
}

// Get complete user data
export const getUserDetailApi = async (
  username: string
): Promise<UserApiResponse> => {
  const response = (await fetchWithConfig(`/api/users/${username}`, {
    method: "GET",
  })) as UserApiResponse;

  return response;
};

// Get user profile only (without posts)
export const getUserProfileApi = async (
  username: string
): Promise<UserProfile> => {
  const response = await getUserDetailApi(username);
  return response.user;
};

// Get user posts only
export const getUserPostsApi = async (
  username: string
): Promise<GetPostResponse[]> => {
  const response = await getUserDetailApi(username);
  return response.posts || [];
};
