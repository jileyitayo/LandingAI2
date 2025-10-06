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
   * Template endpoints
   */
  templates: {
    /**
     * List all templates (system + user's templates)
     * Requires: Authorization header with valid access token
     */
    list: () =>
      apiRequest<
        Array<{
          id: string;
          user_id: string | null;
          name: string;
          description: string | null;
          preview_image: string | null;
          category: string | null;
          tags: string[] | null;
          is_system_template: boolean;
          is_active: boolean;
          is_public: boolean;
          use_count: number;
          created_at: string;
          updated_at: string;
        }>
      >("/api/v1/templates"),

    /**
     * Get specific template by ID
     * Requires: Authorization header with valid access token
     */
    get: (id: string) =>
      apiRequest<{
        id: string;
        user_id: string | null;
        name: string;
        description: string | null;
        preview_image: string | null;
        preview_html: string | null;
        category: string | null;
        tags: string[] | null;
        base_html: string | null;
        base_css: string | null;
        base_js: string | null;
        generation_prompt: string | null;
        style_config: Record<string, any> | null;
        sections_config: Record<string, any>;
        content_schema: Record<string, any> | null;
        is_system_template: boolean;
        is_active: boolean;
        is_public: boolean;
        generation_status: string;
        generation_error: string | null;
        use_count: number;
        created_at: string;
        updated_at: string;
      }>(`/api/v1/templates/${id}`),
    /**
     * Check template generation status
     * Requires: Authorization header with valid access token
     */
    getStatus: (id: string) =>
      apiRequest<{
        status: string;
        template_id: string | null;
        error: string | null;
      }>(`/api/v1/templates/${id}/status`),

    /**
     * Update user's template
     * Requires: Authorization header with valid access token
     */
    update: (
      id: string,
      data: {
        name?: string;
        description?: string;
        category?: string;
        tags?: string[];
      }
    ) =>
      apiRequest<{
        id: string;
        message: string;
      }>(`/api/v1/templates/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),

    /**
     * Delete user's template
     * Requires: Authorization header with valid access token
     */
    delete: (id: string) =>
      apiRequest<{ message: string }>(`/api/v1/templates/${id}`, {
        method: "DELETE",
      }),
  },

  /**
   * Project endpoints
   */
  projects: {
    /**
     * List all user projects
     * Requires: Authorization header with valid access token
     */
    list: () =>
      apiRequest<
        Array<{
          id: string;
          user_id: string;
          name: string;
          description: string | null;
          prompt: string | null;
          template_id: string | null;
          published: boolean;
          subdomain: string | null;
          deployment_url: string | null;
          generation_status: string;
          created_at: string;
          updated_at: string;
        }>
      >("/api/v1/projects"),

    /**
     * Get specific project by ID
     * Requires: Authorization header with valid access token
     */
    get: (id: string) =>
      apiRequest<{
        id: string;
        user_id: string;
        name: string;
        description: string | null;
        prompt: string | null;
        template_id: string | null;
        html_content: string | null;
        css_content: string | null;
        js_content: string | null;
        published: boolean;
        subdomain: string | null;
        deployment_url: string | null;
        theme_settings: Record<string, any> | null;
        whatsapp_number: string | null;
        seo_title: string | null;
        seo_description: string | null;
        generation_status: string;
        generation_error: string | null;
        created_at: string;
        updated_at: string;
      }>(`/api/v1/projects/${id}`),

    /**
     * Create/Generate new project
     * Requires: Authorization header with valid access token
     */
    create: (data: { name: string; prompt: string; template_id?: string }) =>
      apiRequest<{
        id: string;
        status: string;
        message: string;
      }>("/api/v1/projects", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    /**
     * Update project
     * Requires: Authorization header with valid access token
     */
    update: (
      id: string,
      data: {
        name?: string;
        description?: string;
        html_content?: string;
        css_content?: string;
        js_content?: string;
        theme_settings?: Record<string, any>;
        whatsapp_number?: string;
        subdomain?: string;
        seo_title?: string;
        seo_description?: string;
        published?: boolean;
      }
    ) =>
      apiRequest<{
        id: string;
        message: string;
      }>(`/api/v1/projects/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),

    /**
     * Delete project
     * Requires: Authorization header with valid access token
     */
    delete: (id: string) =>
      apiRequest<{ message: string }>(`/api/v1/projects/${id}`, {
        method: "DELETE",
      }),

    /**
     * Publish/Deploy project
     * Requires: Authorization header with valid access token
     */
    publish: (id: string) =>
      apiRequest<{
        id: string;
        deployment_url: string;
        message: string;
      }>(`/api/v1/projects/${id}/publish`, {
        method: "POST",
      }),

    /**
     * Unpublish project
     * Requires: Authorization header with valid access token
     */
    unpublish: (id: string) =>
      apiRequest<{ message: string }>(`/api/v1/projects/${id}/unpublish`, {
        method: "POST",
      }),

    /**
     * Duplicate project
     * Requires: Authorization header with valid access token
     */
    duplicate: (id: string, newName?: string) =>
      apiRequest<{
        id: string;
        message: string;
        name: string;
      }>(`/api/v1/projects/${id}/duplicate`, {
        method: "POST",
        body: JSON.stringify({ new_name: newName }),
      }),

    /**
     * Check subdomain availability
     * Requires: Authorization header with valid access token
     */
    // checkSubdomain: (subdomain: string) =>
    //   apiRequest<{
    //     available: boolean;
    //     subdomain: string;
    //     suggestions: string[];
    //   }>(`/api/v1/projects/subdomain/check/${subdomain}`),
  },

  /**
   * Generation endpoints
   */
  generation: {
    /**
     * Generate website from prompt
     * Requires: Authorization header with valid access token
     */
    generateWebsite: (data: {
      prompt: string;
      project_name?: string;
      style_preferences?: Record<string, any>;
    }) =>
      apiRequest<{
        project_id: string;
        status: string;
        message: string;
      }>("/api/v1/generate_website", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    /**
     * Check generation status
     * Requires: Authorization header with valid access token
     */
    getStatus: (projectId: string) =>
      apiRequest<{
        status: string;
        error?: string;
      }>(`/api/v1/generation/${projectId}/status`),
  },

  /**
   * Deployment endpoints
   */
  deployment: {
    /**
     * Deploy project to Vercel
     * Requires: Authorization header with valid access token
     */
    deploy: (projectId: string) =>
      apiRequest<{
        deployment_id: string;
        deployment_url: string;
        status: string;
        deployed_at: string;
      }>(`/api/v1/projects/${projectId}/deploy`, {
        method: "POST",
      }),

    /**
     * Delete project deployment from Vercel
     * Requires: Authorization header with valid access token
     */
    deleteDeployment: (projectId: string) =>
      apiRequest<{
        message: string;
        project_id: string;
      }>(`/api/v1/projects/${projectId}/deploy`, {
        method: "DELETE",
      }),

    /**
     * Get deployment status
     * Requires: Authorization header with valid access token
     */
    getStatus: (projectId: string) =>
      apiRequest<{
        deployment_id: string | null;
        deployment_url: string | null;
        state: string;
        ready: boolean;
        last_deployed_at: string | null;
      }>(`/api/v1/projects/${projectId}/deployment-status`),
  },
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
