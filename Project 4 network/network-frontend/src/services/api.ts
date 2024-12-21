export const API_BASE_URL = "http://localhost:8000";

function getCsrfToken(): string {
  return (
    document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="))
      ?.split("=")[1] ?? ""
  );
}

export const fetchWithConfig = async (
  endpoint: string,
  options?: RequestInit
) => {
  const normalizedEndpoint = endpoint.startsWith("/")
    ? endpoint
    : `/${endpoint}`;

  const headers = {
    "Content-Type": "application/json",
    "X-CSRFToken": getCsrfToken(),
    ...(options?.headers || {}),
  };

  const response = await fetch(`${API_BASE_URL}${normalizedEndpoint}`, {
    ...options,
    credentials: "include",
    headers,
  });

  // First check if response has content
  const contentType = response.headers.get("content-type");

  if (contentType?.includes("application/json")) {
    try {
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "An error occurred");
      }
      return data;
    } catch (error) {
      console.error("JSON parsing error:", error);
      throw new Error("Invalid response format from server");
    }
  }

  // Handle non-JSON responses
  if (!response.ok) {
    throw new Error("Network response was not ok");
  }

  return null;
};
