import { fetchWithConfig } from "./api";

export interface LoginResponse {
  message: string;
  user: {
    id: number;
    username: string;
    email: string;
    following_count: number;
    follower_count: number;
  };
}

export const loginUser = async (username: string, password: string) => {
  const data = await fetchWithConfig("login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  return data as LoginResponse;
};

export const logoutUser = async () => {
  return fetchWithConfig("/logout", {
    method: "POST",
  });
};

export const checkAuthStatus = async () => {
  const data = await fetchWithConfig("check_auth", {
    method: "GET",
  });
  return data as LoginResponse;
};
