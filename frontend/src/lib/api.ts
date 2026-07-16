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

  /**
   * Extract user-friendly error message from validation errors
   * Handles FastAPI validation error format
   */
  getValidationMessage(): string {
    // Check if detail.detail is an array (FastAPI validation errors)
    const validationErrors = this.detail?.detail || this.detail;

    if (Array.isArray(validationErrors)) {
      // Extract the first validation error message
      const firstError = validationErrors[0];
      if (firstError && firstError.msg) {
        return firstError.msg;
      }
    }

    return this.message;
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
 * Custom domain state for a project (see backend routers/domains.py)
 */
export interface DomainStatus {
  domain: string | null;
  status: 'pending_dns' | 'verified' | 'error' | null;
  verified: boolean;
  misconfigured: boolean;
  dns_instructions: Array<{ type: string; name: string; value: string }>;
  error: string | null;
  checked_at: string | null;
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
        subscription?: {
          id: string;
          status: string;
          tier: {
            id: string;
            tier_name: string;
            display_name: string;
            description: string | null;
            daily_generation_limit: number;
            per_minute_limit: number;
            price_monthly: number;
            price_yearly: number;
            features: string[];
            is_active: boolean;
          };
          current_period_start: string | null;
          current_period_end: string | null;
          cancel_at_period_end: boolean;
          cancelled_at: string | null;
          trial_start: string | null;
          trial_end: string | null;
        };
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

    /**
     * Get usage analytics
     * Requires: Authorization header with valid access token
     * @param period - Time period: 24h, 7d, 30d, or all
     * @param granularity - Data granularity: hourly or daily
     */
    getAnalytics: (period: "24h" | "7d" | "30d" | "all" = "7d", granularity: "hourly" | "daily" = "daily") =>
      apiRequest<{
        period: string;
        granularity: string;
        data_points: Array<{
          timestamp: string;
          count: number;
          call_types: Record<string, number>;
        }>;
        total_calls: number;
        rpm_peak: number;
        rpd_average: number;
        breakdown_by_type: Record<string, number>;
      }>(`/api/v1/users/analytics?period=${period}&granularity=${granularity}`),
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
     * List all user projects with optional pagination and filters
     * Requires: Authorization header with valid access token
     */
    list: (params?: {
      limit?: number;
      offset?: number;
      status_filter?: string;
      search?: string;
    }) => {
      const queryParams = new URLSearchParams();
      if (params?.limit) queryParams.append("limit", params.limit.toString());
      if (params?.offset) queryParams.append("offset", params.offset.toString());
      if (params?.status_filter) queryParams.append("status_filter", params.status_filter);
      if (params?.search) queryParams.append("search", params.search);

      const queryString = queryParams.toString();
      const endpoint = `/api/v1/projects${queryString ? `?${queryString}` : ''}`;

      return apiRequest<
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
          thumbnail_url: string | null;
          generation_status: string;
          created_at: string;
          updated_at: string;
        }>
      >(endpoint);
    },

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
        project_type?: 'html' | 'react';
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
        favicon_url?: string;
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
     * Download React project as ZIP file
     * Requires: Authorization header with valid access token
     * @param id - Project ID
     * @returns Promise that resolves with the download response
     */
    download: async (id: string): Promise<Response> => {
      const token = await getAccessToken();
      
      const response = await fetch(`${API_BASE_URL}/api/v1/projects/${id}/download`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          response.status,
          errorData.detail || response.statusText,
          errorData
        );
      }
      return response;
    },

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
    checkSubdomain: (subdomain: string) =>
      apiRequest<{
        available: boolean;
        subdomain: string;
        suggestions: string[];
      }>(`/api/v1/projects/subdomain/check/${subdomain}`),
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
      attachments?: Array<{ media_id: string; url: string; media_type?: string }>;
      skip_clarification?: boolean;
      clarification_response?: string;
    }) =>
      apiRequest<{
        project_id: string | null;
        status: string; // "generating" | "needs_clarification"
        message: string;
        clarification?: {
          question: string;
          wants_attachment: boolean;
          reason: string;
          url?: string | null;
        };
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
        project_id?: string;
        progress?: number; // 0-100
        stage?: string; // Current generation stage (e.g., "analyzing", "generating_structure", etc.)
        stage_message?: string; // Human-readable stage message
        message?: string;
        error?: string;
        created_at?: string;
        completed_at?: string;
      }>(`/api/v1/generation/${projectId}/status`),

    /**
     * Create preview of React project
     * Builds project and returns preview URL
     */
    createPreview: (projectId: string) =>
      apiRequest<{
        preview_id: string;
        preview_url: string;
        expires_at: string;
      }>(`/api/v1/preview/${projectId}`, {
        method: "POST",
      }),

    /**
     * Get React project files
     */
    getReactProject: (projectId: string) =>
      apiRequest<{
        project_id: string;
        name: string;
        status: string;
        files: Record<string, string>;
        files_count: number;
      }>(`/api/v1/react_website/${projectId}`),

    /**
     * Edit React component(s) using visual selection and natural language.
     * Supports multi-select (selected_elements) and scope (element | section | page).
     * The backend verifies the edit compiles and returns the new preview URL.
     */
    editComponent: (projectId: string, data: {
      selected_element?: Record<string, any>;
      selected_elements?: Record<string, any>[];
      scope?: 'element' | 'section' | 'page';
      instruction: string;
      attachments?: Array<{ media_id: string; url: string; media_type?: string }>;
      current_route?: string;
      confirmed_target?: string;
      confirmed_page?: Record<string, any>;
      skip_clarification?: boolean;
      clarification_response?: string;
    }) =>
      apiRequest<{
        success: boolean;
        message: string;
        updated_file?: string;
        updated_files?: string[];
        preview_url?: string;
        preview_id?: string;
        old_code?: string;
        new_code?: string;
        edit_description?: string;
        chat_message_id?: string;
        needs_confirmation?: boolean;
        confirmation?: Record<string, any>;
      }>(`/api/v1/edit/project/${projectId}`, {
        method: "POST",
        body: JSON.stringify(data),
      }),

    /**
     * Streaming edit: same as editComponent but yields live stage events
     * (analyzing → editing → building → done|error) via SSE. Calls onProgress
     * for each stage and resolves with the final result. Throws on stream error
     * so callers can fall back to the non-streaming editComponent.
     */
    editComponentStream: async (
      projectId: string,
      data: {
        selected_element?: Record<string, any>;
        selected_elements?: Record<string, any>[];
        scope?: 'element' | 'section' | 'page';
        instruction: string;
        attachments?: Array<{ media_id: string; url: string; media_type?: string }>;
        current_route?: string;
        confirmed_target?: string;
        confirmed_page?: Record<string, any>;
        skip_clarification?: boolean;
        clarification_response?: string;
      },
      onProgress: (stage: string, detail: string) => void
    ): Promise<{
      success: boolean;
      message: string;
      updated_file?: string;
      updated_files?: string[];
      preview_url?: string;
      preview_id?: string;
      old_code?: string;
      new_code?: string;
      edit_description?: string;
      chat_message_id?: string;
      needs_confirmation?: boolean;
      confirmation?: Record<string, any>;
    }> => {
      const token = await getAccessToken();
      const response = await fetch(`${API_BASE_URL}/api/v1/edit/project/${projectId}/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok || !response.body) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(response.status, errorData.detail || response.statusText, errorData);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let result: any = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // SSE frames are separated by a blank line
        const frames = buffer.split("\n\n");
        buffer = frames.pop() ?? "";
        for (const frame of frames) {
          const line = frame.split("\n").find((l) => l.startsWith("data: "));
          if (!line) continue;
          const event = JSON.parse(line.slice(6));
          if (event.type === "progress") {
            onProgress(event.stage, event.detail);
          } else if (event.type === "result") {
            result = event.data;
          } else if (event.type === "error") {
            throw new ApiError(event.status || 500, event.detail || "Edit failed", event);
          }
        }
      }

      if (!result) {
        throw new ApiError(500, "Edit stream ended without a result");
      }
      return result;
    },

    /**
     * Edit React component properties directly (click-to-edit system)
     */
    editProperties: (projectId: string, data: {
      element_selector: string;
      component_file: string;
      properties: Array<{
        property: string;
        value: string | number | boolean;
        oldValue?: string | number | boolean;
        unit?: string;
      }>;
      batch?: boolean;
    }) =>
      apiRequest<{
        success: boolean;
        message: string;
        updated_file: string;
        changes_applied: Array<{
          property: string;
          value: string | number | boolean;
          oldValue?: string | number | boolean;
        }>;
        preview_url?: string;
        new_code?: string;
        old_code?: string;
        prop_edit_info?: {
          prop_name: string;
          source_file: string;
          new_value: string | number | boolean;
        };
      }>(`/api/v1/edit/project/${projectId}/properties`, {
        method: "POST",
        body: JSON.stringify(data),
      }),

    /**
     * Get chat history for a project
     */
    getChatHistory: (projectId: string) =>
      apiRequest<{
        messages: Array<{
          id: string;
          project_id: string;
          user_id: string;
          message_type: 'generation' | 'edit' | 'question';
          user_prompt: string;
          ai_response: string;
          metadata: Record<string, any>;
          created_at: string;
          updated_at: string;
        }>;
        total_count: number;
      }>(`/api/v1/projects/${projectId}/chat-history`),

    /**
     * Get edit history (grouped per AI edit) for the undo/history panel
     */
    getEditHistory: (projectId: string) =>
      apiRequest<{
        edits: Array<{
          chat_message_id: string;
          instruction: string;
          edit_description: string | null;
          created_at: string;
          files: Array<{ file_path: string; is_reverted: boolean }>;
          is_reverted: boolean;
          can_revert: boolean;
        }>;
      }>(`/api/v1/projects/${projectId}/edit-history`),

    /**
     * Get each page's reorderable sections
     */
    getPageStructure: (projectId: string) =>
      apiRequest<{
        pages: Array<{
          page_file: string;
          page_name: string;
          sections: Array<{ id: number; name: string; is_component: boolean }>;
        }>;
      }>(`/api/v1/projects/${projectId}/page-structure`),

    /**
     * Reorder a page's sections (deterministic, undoable)
     */
    reorderSections: (projectId: string, pageFile: string, order: number[]) =>
      apiRequest<{
        success: boolean;
        message: string;
        preview_url?: string;
        preview_id?: string;
      }>(`/api/v1/projects/${projectId}/pages/reorder`, {
        method: "POST",
        body: JSON.stringify({ page_file: pageFile, order }),
      }),

    /**
     * Revert (undo) an AI edit — restores every file it touched to pre-edit code
     */
    revertEdit: (projectId: string, chatMessageId: string) =>
      apiRequest<{
        success: boolean;
        message: string;
        reverted_files: string[];
        preview_url?: string;
        preview_id?: string;
      }>(`/api/v1/projects/${projectId}/edits/${chatMessageId}/revert`, {
        method: "POST",
      }),

    /**
     * Save a chat message
     */
    saveChatMessage: (projectId: string, data: {
      message_type: 'generation' | 'edit' | 'question';
      user_prompt: string;
      ai_response: string;
      metadata?: Record<string, any>;
    }) =>
      apiRequest<{
        id: string;
        project_id: string;
        user_id: string;
        message_type: string;
        user_prompt: string;
        ai_response: string;
        metadata: Record<string, any>;
        created_at: string;
        updated_at: string;
      }>(`/api/v1/projects/${projectId}/chat-messages`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },

  /**
   * Media endpoints (image uploads for chat attachments, site assets, favicons)
   */
  media: {
    /**
     * Upload a media file (image).
     * project_id is optional — dashboard uploads happen before a project exists.
     */
    upload: async (file: File, options?: { projectId?: string; purpose?: 'attachment' | 'favicon' }) => {
      const token = await getAccessToken();
      const formData = new FormData();
      formData.append("file", file);
      if (options?.projectId) formData.append("project_id", options.projectId);
      if (options?.purpose) formData.append("purpose", options.purpose);

      const response = await fetch(`${API_BASE_URL}/api/v1/media`, {
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
        id: string;
        project_id: string | null;
        public_url: string;
        media_type: string;
        mime_type: string;
        original_filename: string | null;
        size_bytes: number;
        width: number | null;
        height: number | null;
        purpose: string;
        created_at: string | null;
      }>;
    },

    /**
     * List media attached to a project
     */
    list: (projectId: string) =>
      apiRequest<{
        media: Array<{
          id: string;
          project_id: string | null;
          public_url: string;
          media_type: string;
          mime_type: string;
          original_filename: string | null;
          size_bytes: number;
          width: number | null;
          height: number | null;
          purpose: string;
          created_at: string | null;
        }>;
      }>(`/api/v1/projects/${projectId}/media`),

    /**
     * Delete a media file
     */
    delete: (mediaId: string) =>
      apiRequest<{ message: string }>(`/api/v1/media/${mediaId}`, {
        method: "DELETE",
      }),
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
        status: string;
        message: string;
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
        last_edited_at: string | null;
        has_unpublished_changes: boolean;
        deploy_status: 'idle' | 'queued' | 'uploading' | 'building' | 'ready' | 'error';
        deploy_stage_detail: string | null;
        deploy_error: string | null;
      }>(`/api/v1/projects/${projectId}/deployment-status`),
  },

  /**
   * Custom domain endpoints (Pro tier)
   */
  domains: {
    /**
     * Connect a custom domain to a published project
     * Requires: Authorization header with valid access token; Pro/Premium plan
     */
    set: (projectId: string, domain: string) =>
      apiRequest<DomainStatus>(`/api/v1/projects/${projectId}/domain`, {
        method: "POST",
        body: JSON.stringify({ domain }),
      }),

    /**
     * Get custom domain status (live-checks Vercel; poll target)
     * Requires: Authorization header with valid access token
     */
    getStatus: (projectId: string) =>
      apiRequest<DomainStatus>(`/api/v1/projects/${projectId}/domain`),

    /**
     * Disconnect the project's custom domain
     * Requires: Authorization header with valid access token
     */
    remove: (projectId: string) =>
      apiRequest<{ message: string; project_id: string }>(
        `/api/v1/projects/${projectId}/domain`,
        { method: "DELETE" }
      ),
  },

  /**
   * Feedback endpoints
   */
  feedback: {
    /**
     * Submit user feedback or feature request
     * Requires: Authorization header with valid access token
     */
    submit: (data: {
      rating?: number;
      message: string;
      category?: 'general' | 'bug' | 'feature' | 'ui/ux' | 'other';
      action?: 'create_project' | 'edit_project' | 'generate_website' | 'edit_component' |
               'edit_properties' | 'publish_deploy' | 'download_project' | 'manage_settings' |
               'upload_avatar' | 'view_analytics' | 'duplicate_project' | 'delete_project' |
               'code_editing' | 'preview_project' | 'other';
      project_id?: string;
    }) =>
      apiRequest<{
        id: string;
        message: string;
      }>("/api/v1/feedback", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    /**
     * Get current user's feedback history
     * Requires: Authorization header with valid access token
     */
    list: (params?: { limit?: number; offset?: number }) => {
      const queryParams = new URLSearchParams();
      if (params?.limit) queryParams.append("limit", params.limit.toString());
      if (params?.offset) queryParams.append("offset", params.offset.toString());

      const queryString = queryParams.toString();
      const endpoint = `/api/v1/feedback${queryString ? `?${queryString}` : ''}`;

      return apiRequest<{
        feedback: Array<{
          id: string;
          user_id: string;
          rating: number | null;
          message: string;
          category: string;
          action: string | null;
          project_id: string | null;
          is_resolved: boolean;
          created_at: string;
          updated_at: string;
        }>;
        total: number;
        limit: number;
        offset: number;
      }>(endpoint);
    },

    /**
     * Get a specific feedback by ID
     * Requires: Authorization header with valid access token
     */
    get: (feedbackId: string) =>
      apiRequest<{
        id: string;
        user_id: string;
        rating: number | null;
        message: string;
        category: string;
        action: string | null;
        project_id: string | null;
        is_resolved: boolean;
        created_at: string;
        updated_at: string;
      }>(`/api/v1/feedback/${feedbackId}`),
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
