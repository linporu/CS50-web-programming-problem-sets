export const API_BASE_URL = "http://localhost:8000";

// Track CSRF token initialization state
let csrfTokenInitialized = false;

// Get CSRF token from cookies
function getCsrfToken(): string {
  return (
    document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="))
      ?.split("=")[1] ?? ""
  );
}

// Ensure CSRF token is set
async function ensureCsrfToken() {
  if (!csrfTokenInitialized && !getCsrfToken()) {
    await fetch(`${API_BASE_URL}/csrf`, {
      credentials: "include",
    });
    csrfTokenInitialized = getCsrfToken() !== "";
  }
}

export const fetchWithConfig = async (
  endpoint: string,
  options?: RequestInit
) => {
  // Ensure CSRF token exists before each request
  await ensureCsrfToken();

  const normalizedEndpoint = endpoint.startsWith("/")
    ? endpoint
    : `/${endpoint}`;

  const response = await fetch(`${API_BASE_URL}${normalizedEndpoint}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
      ...(options?.headers || {}),
    },
  });

  // Add more robust header checking
  if (!response.headers) {
    return null;
  }

  const contentType = response.headers.get("content-type");
  if (!contentType) {
    return null;
  }

  if (contentType.includes("application/json")) {
    try {
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "An error occurred");
      }
      return data;
    } catch (error) {
      if (!response.ok) {
        throw error;
      }
      console.error("JSON parsing error:", error);
      throw new Error("Invalid response format from server");
    }
  }

  // For non-JSON responses, just return null
  return null;
};
