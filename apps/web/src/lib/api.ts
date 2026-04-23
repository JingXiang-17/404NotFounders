export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultHeaders: HeadersInit = {
    // Add default headers if necessary
  };

  // Only set application/json if we are not sending FormData
  if (!(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, {
    ...options,
    cache: "no-store",
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    let message = `API request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      if (typeof payload?.detail === "string" && payload.detail) {
        message = payload.detail;
      }
    } catch {
      // Fall back to default message.
    }
    throw new Error(message);
  }

  return response.json();
}
