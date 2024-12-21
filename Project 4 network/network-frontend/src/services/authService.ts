import { fetchWithConfig } from "./api";

interface LoginResponse {
  message: string;
  user: {
    id: number;
    username: string;
    email: string;
    following_count: number;
    follower_count: number;
  };
}

// Function to get CSRF token
function getCsrfToken(): string {
  // Django stores CSRF token in a cookie named csrftoken
  return (
    document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="))
      ?.split("=")[1] ?? ""
  );
}

async function ensureCsrfToken() {
  // Send request to Django backend to get CSRF token
  await fetch("http://localhost:8000/csrf", {
    credentials: "include",
  });
}

export const loginUser = async (username: string, password: string) => {
  try {
    // Ensure CSRF token is present before login
    await ensureCsrfToken();

    const data = await fetchWithConfig("login", {
      method: "POST",
      headers: {
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ username, password }),
    });
    return data as LoginResponse;
  } catch (error) {
    throw error;
  }
};

export const logoutUser = async () => {
  return fetchWithConfig("/logout", {
    method: "POST",
  });
};
