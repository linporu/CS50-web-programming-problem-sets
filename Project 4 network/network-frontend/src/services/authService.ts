import { fetchWithConfig } from "./api";

export const loginUser = async (username: string, password: string) => {
  return fetchWithConfig("/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
};

export const logoutUser = async () => {
  return fetchWithConfig("/logout", {
    method: "POST",
  });
};
