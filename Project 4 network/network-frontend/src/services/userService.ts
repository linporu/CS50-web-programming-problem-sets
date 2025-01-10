import { fetchWithConfig } from "./api";
import { Post } from "./postService";

interface UserApiResponse {
  message: string;
  user: {
    username: string;
    email: string;
    following_count: number;
    follower_count: number;
    is_following: boolean;
  };
  posts: Post[] | null;
}

export interface UserProfile {
  username: string;
  email: string;
  following_count: number;
  follower_count: number;
  is_following: boolean;
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
export const getUserPostsApi = async (username: string): Promise<Post[]> => {
  const response = await getUserDetailApi(username);
  return response.posts || [];
};

interface FollowApiResponse {
  message: string;
  data: {
    following_count: number;
    follower_count: number;
  };
}

export const followUserApi = async (
  username: string
): Promise<FollowApiResponse> => {
  const response = (await fetchWithConfig(`/api/users/${username}/follow`, {
    method: "POST",
  })) as FollowApiResponse;
  return response;
};

export const unfollowUserApi = async (
  username: string
): Promise<FollowApiResponse> => {
  const response = (await fetchWithConfig(`/api/users/${username}/follow`, {
    method: "DELETE",
  })) as FollowApiResponse;
  return response;
};
