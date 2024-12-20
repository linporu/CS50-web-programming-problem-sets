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

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error);
  }

  return data;
};
