/**
 * API client for communicating with the FastAPI backend
 * Handles authentication headers and error responses
 */

import { createClient } from "@/lib/supabase/client";

// Backend API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public detail?: any
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Get the current user's access token from Supabase
 * @returns Access token or null if not authenticated
 */
async function getAccessToken(): Promise<string | null> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return session?.access_token ?? null;
}

/**
 * Make an authenticated API request
 * Automatically includes Authorization header with Supabase access token
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAccessToken();

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  // Only add Content-Type if not already set (for file uploads)
  if (!headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  // Add Authorization header if token exists
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle non-OK responses
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.detail || response.statusText,
      errorData
    );
  }

  // Return JSON response
  return response.json();
}

/**
 * API client with typed methods for backend endpoints
 */
export const api = {
  /**
   * Health check endpoint
   */
  health: {
    check: () => apiRequest<{ status: string; timestamp: string }>("/api/v1/health"),
  },

  /**
   * Authentication endpoints
   */
  auth: {
    /**
     * Get current authenticated user from backend
     * Requires: Authorization header with valid access token
     */
    getUser: () =>
      apiRequest<{
        id: string;
        email: string;
        first_name?: string;
        last_name?: string;
        created_at: string;
        updated_at: string;
      }>("/api/v1/auth/user"),

    /**
     * Sign up a new user
     * Note: This calls the backend, but you may prefer using Supabase directly
     */
    signup: (data: {
      email: string;
      password: string;
      first_name?: string;
      last_name?: string;
    }) =>
      apiRequest<{
        access_token: string;
        refresh_token: string;
        expires_in: number;
        token_type: string;
        user: {
          id: string;
          email: string;
          created_at: string;
        };
      }>("/api/v1/auth/signup", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    /**
     * Login user
     * Note: This calls the backend, but you may prefer using Supabase directly
     */
    login: (data: { email: string; password: string }) =>
      apiRequest<{
        access_token: string;
        refresh_token: string;
        expires_in: number;
        token_type: string;
        user: {
          id: string;
          email: string;
          created_at: string;
        };
      }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    /**
     * Logout current user (invalidate session on backend)
     * Requires: Authorization header with valid access token
     */
    logout: () =>
      apiRequest<{ message: string }>("/api/v1/auth/logout", {
        method: "POST",
      }),

    /**
     * Refresh access token
     * Note: This calls the backend, but you may prefer using Supabase directly
     */
    refresh: (refreshToken: string) =>
      apiRequest<{
        access_token: string;
        refresh_token: string;
        expires_in: number;
        token_type: string;
        user: {
          id: string;
          email: string;
          created_at: string;
        };
      }>("/api/v1/auth/refresh", {
        method: "POST",
        body: JSON.stringify({ refresh_token: refreshToken }),
      }),
  },

  /**
   * User profile endpoints
   */
  users: {
    /**
     * Get current user profile
     * Requires: Authorization header with valid access token
     */
    getProfile: () =>
      apiRequest<{
        id: string;
        email: string;
        first_name: string | null;
        last_name: string | null;
        avatar_url: string | null;
        subscription_tier: string;
        generation_count: number;
        current_period_generations: number;
        email_verified: boolean;
        created_at: string;
        updated_at: string;
      }>("/api/v1/users/profile"),

    /**
     * Update current user profile
     * Requires: Authorization header with valid access token
     */
    updateProfile: (data: { first_name?: string; last_name?: string }) =>
      apiRequest<{
        id: string;
        email: string;
        first_name: string | null;
        last_name: string | null;
        avatar_url: string | null;
        subscription_tier: string;
        generation_count: number;
        current_period_generations: number;
        email_verified: boolean;
        created_at: string;
        updated_at: string;
      }>("/api/v1/users/profile", {
        method: "PATCH",
        body: JSON.stringify(data),
      }),

    /**
     * Upload user avatar
     * Requires: Authorization header with valid access token
     * @param file - Image file to upload (jpg, png, gif, webp)
     */
    uploadAvatar: async (file: File) => {
      const token = await getAccessToken();
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_BASE_URL}/api/v1/users/avatar`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          // Don't set Content-Type for FormData - browser sets it automatically with boundary
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          response.status,
          errorData.detail || response.statusText,
          errorData
        );
      }

      return response.json() as Promise<{
        avatar_url: string;
        message: string;
      }>;
    },
  },

  /**
   * Example of how to add more API endpoints
   * 
   * projects: {
   *   list: () => apiRequest<Project[]>("/api/v1/projects"),
   *   get: (id: string) => apiRequest<Project>(`/api/v1/projects/${id}`),
   *   create: (data: CreateProjectData) =>
   *     apiRequest<Project>("/api/v1/projects", {
   *       method: "POST",
   *       body: JSON.stringify(data),
   *     }),
   *   update: (id: string, data: UpdateProjectData) =>
   *     apiRequest<Project>(`/api/v1/projects/${id}`, {
   *       method: "PUT",
   *       body: JSON.stringify(data),
   *     }),
   *   delete: (id: string) =>
   *     apiRequest<void>(`/api/v1/projects/${id}`, {
   *       method: "DELETE",
   *     }),
   * },
   */
};

/**
 * Server-side API client for use in Server Components and Server Actions
 * Requires passing the session/token explicitly
 */
export async function serverApiRequest<T>(
  endpoint: string,
  token: string | null,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // Add Authorization header if token exists
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
    cache: "no-store", // Disable caching for server-side requests
  });

  // Handle non-OK responses
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.detail || response.statusText,
      errorData
    );
  }

  // Return JSON response
  return response.json();
}
