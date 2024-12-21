export const API_BASE_URL = "http://localhost:8000";

export const fetchWithConfig = async (
  endpoint: string,
  options?: RequestInit
) => {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  // First check if response has content
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    const data = await response.json();

    // Handle error responses
    if (!response.ok) {
      throw new Error(data.error || "An error occurred");
    }

    return data;
  }

  // Handle non-JSON responses
  if (!response.ok) {
    throw new Error("Network response was not ok");
  }

  return null;
};
