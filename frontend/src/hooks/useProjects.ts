/**
 * Custom hook for managing projects data with SWR
 * Provides data fetching, caching, and optimistic updates
 */

import useSWR, { mutate } from "swr";
import { api } from "@/lib/api";

/**
 * Project type as returned by the API
 */
export interface Project {
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
}

/**
 * Parameters for fetching projects with pagination and filters
 */
export interface ProjectsParams {
  page?: number;
  limit?: number;
  status_filter?: string;
  search?: string;
}

/**
 * Hook for fetching user projects with pagination, caching and auto-revalidation
 */
export function useProjects(params: ProjectsParams = {}) {
  const { page = 1, limit = 12, status_filter, search } = params;
  const offset = (page - 1) * limit;

  // Create a unique SWR key that includes all parameters
  const key = {
    url: "/api/v1/projects",
    page,
    limit,
    status_filter,
    search,
  };

  const { data, error, isLoading, mutate: mutateProjects } = useSWR<Project[]>(
    key,
    () => api.projects.list({ limit, offset, status_filter, search }),
    {
      // Revalidate on focus to keep data fresh
      revalidateOnFocus: true,
      // Revalidate on reconnect
      revalidateOnReconnect: true,
      // Dedupe requests within 2 seconds
      dedupingInterval: 2000,
      // Keep previous data while revalidating
      keepPreviousData: true,
    }
  );

  return {
    projects: data,
    isLoading,
    isError: error,
    mutate: mutateProjects,
  };
}

/**
 * Hook for deleting a project with optimistic updates
 * Works with paginated project lists
 */
export function useDeleteProject() {
  const deleteProject = async (projectId: string) => {
    // Perform the actual deletion
    await api.projects.delete(projectId);

    // Revalidate all project lists (with different pagination/filter params)
    await mutate(
      (key: any) => typeof key === 'object' && key?.url === '/api/v1/projects',
      undefined,
      { revalidate: true }
    );
  };

  return { deleteProject };
}

/**
 * Hook for duplicating a project
 * Works with paginated project lists
 */
export function useDuplicateProject() {
  const duplicateProject = async (projectId: string) => {
    try {
      // Call the API to duplicate
      const result = await api.projects.duplicate(projectId);

      // Revalidate all project lists to show the new duplicate
      await mutate(
        (key: any) => typeof key === 'object' && key?.url === '/api/v1/projects',
        undefined,
        { revalidate: true }
      );

      return result;
    } catch (error) {
      console.error("Failed to duplicate project:", error);
      throw error;
    }
  };

  return { duplicateProject };
}

/**
 * Hook for user profile with caching
 */
export function useUserProfile() {
  const { data, error, isLoading } = useSWR(
    "/api/v1/users/profile",
    api.users.getProfile,
    {
      // Profile data changes less frequently, so revalidate less often
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      // Cache for 5 minutes
      dedupingInterval: 300000,
    }
  );

  return {
    profile: data,
    isLoading,
    isError: error,
  };
}
