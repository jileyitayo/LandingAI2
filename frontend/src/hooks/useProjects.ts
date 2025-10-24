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
  generation_status: string;
  created_at: string;
  updated_at: string;
}

/**
 * Hook for fetching all user projects with caching and auto-revalidation
 */
export function useProjects() {
  const { data, error, isLoading, mutate: mutateProjects } = useSWR<Project[]>(
    "/api/v1/projects",
    api.projects.list,
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
 */
export function useDeleteProject() {
  const deleteProject = async (projectId: string) => {
    // Optimistically update the UI by filtering out the deleted project
    await mutate(
      "/api/v1/projects",
      async (currentProjects: Project[] | undefined) => {
        if (!currentProjects) return currentProjects;

        // Optimistically remove the project
        const optimisticData = currentProjects.filter((p) => p.id !== projectId);

        try {
          // Perform the actual deletion
          await api.projects.delete(projectId);
          return optimisticData;
        } catch (error) {
          // If deletion fails, revert by returning current data
          throw error;
        }
      },
      {
        // Don't revalidate immediately to show optimistic update
        revalidate: false,
        // Rollback on error
        rollbackOnError: true,
        // Show optimistic update immediately
        optimisticData: (currentProjects: Project[] | undefined) => {
          if (!currentProjects) return currentProjects;
          return currentProjects.filter((p) => p.id !== projectId);
        },
      }
    );
  };

  return { deleteProject };
}

/**
 * Hook for duplicating a project with optimistic updates
 */
export function useDuplicateProject() {
  const duplicateProject = async (projectId: string) => {
    try {
      // Call the API to duplicate
      const result = await api.projects.duplicate(projectId);

      // Revalidate to get the fresh list including the new project
      await mutate("/api/v1/projects");

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
