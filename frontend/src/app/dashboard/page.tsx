"use client";

/**
 * DashboardPage.tsx
 *
 * Main dashboard displaying all user projects with search and filter capabilities
 */

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import {
  useProjects,
  useDeleteProject,
  useDuplicateProject,
  type Project
} from "@/hooks/useProjects";
import { useDebounce } from "@/hooks/useDebounce";
import ProjectCard from "@/components/ProjectCard";
import Pagination from "@/components/Pagination";
import DashboardHeader from "@/components/DashboardHeader";
import { Plus, Search, Filter } from "lucide-react";

const STATUS_FILTERS = [
  { value: "all", label: "All Projects" },
  { value: "completed", label: "Completed" },
  { value: "generating", label: "Generating" },
  { value: "failed", label: "Failed" },
];

/**
 * Dashboard page - Protected route
 * Displays all user projects with search and filter
 */
export default function DashboardPage() {
  const router = useRouter();
  const { user, loading } = useAuth();

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(12);

  // Filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showFilterMenu, setShowFilterMenu] = useState(false);
  const filterRef = useRef<HTMLDivElement>(null);

  // Close filter menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (filterRef.current && !filterRef.current.contains(event.target as Node)) {
        setShowFilterMenu(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounce search query to reduce API calls while typing
  const debouncedSearchQuery = useDebounce(searchQuery, 500);

  // Fetch data using SWR hooks with pagination and filters
  const { projects, isLoading: projectsLoading } = useProjects({
    page: currentPage,
    limit: itemsPerPage,
    status_filter: statusFilter !== 'all' ? statusFilter : undefined,
    search: debouncedSearchQuery || undefined,
  });

  const { deleteProject } = useDeleteProject();
  const { duplicateProject } = useDuplicateProject();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/login");
    }
  }, [user, loading, router]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [debouncedSearchQuery, statusFilter]);

  // Reset to page 1 when items per page changes
  const handleItemsPerPageChange = (newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1);
  };

  const handleDeleteProject = async (projectId: string) => {
    try {
      // Use SWR optimistic update
      await deleteProject(projectId);
    } catch (error) {
      console.error("Failed to delete project:", error);
      alert("Failed to delete project. Please try again.");
    }
  };

  const handleDuplicateProject = async (projectId: string) => {
    try {
      // Use SWR hook which handles cache revalidation
      await duplicateProject(projectId);
    } catch (error) {
      console.error("Failed to duplicate project:", error);
      alert("Failed to duplicate project. Please try again.");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand mx-auto"></div>
          <p className="mt-4 text-muted">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-surface">
      <DashboardHeader />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8 gap-4">
          <div>
            <h1 className="font-display text-3xl font-bold text-fg">My Projects</h1>
            <p className="mt-1 text-sm text-muted">
              {projects?.length || 0} {projects?.length === 1 ? "project" : "projects"} on this page
            </p>
          </div>

          <button
            onClick={() => router.push("/dashboard/new")}
            className="inline-flex items-center gap-2 px-6 py-3 bg-brand-gradient text-brand-fg font-medium rounded-full shadow-glow-sm hover:shadow-glow hover:-translate-y-0.5 active:translate-y-0 transition-all"
          >
            <Plus className="w-5 h-5" />
            New Project
          </button>
        </div>

        {/* Search and Filter Bar */}
        <div className="mb-6 flex flex-col sm:flex-row gap-3">
          {/* Search Input */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted" />
            <input
              type="text"
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-10"
            />
          </div>

          {/* Status Filter */}
          <div className="relative" ref={filterRef}>
            <button
              onClick={() => setShowFilterMenu(!showFilterMenu)}
              className="inline-flex items-center gap-2 px-4 py-2.5 border border-border rounded-full bg-card hover:bg-card-muted transition-colors min-w-[160px] justify-between"
            >
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-muted" />
                <span className="text-sm font-medium text-fg">
                  {STATUS_FILTERS.find((f) => f.value === statusFilter)?.label}
                </span>
              </div>
              <svg
                className={`w-4 h-4 text-muted transition-transform ${
                  showFilterMenu ? "rotate-180" : ""
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>

            {/* Filter Dropdown */}
            {showFilterMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-card rounded-xl shadow-lg border border-border py-1 z-10">
                {STATUS_FILTERS.map((filter) => (
                  <button
                    key={filter.value}
                    onClick={() => {
                      setStatusFilter(filter.value);
                      setShowFilterMenu(false);
                    }}
                    className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                      statusFilter === filter.value
                        ? "bg-brand/10 text-brand font-medium"
                        : "text-fg hover:bg-card-muted"
                    }`}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Projects Grid */}
        {projectsLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand mx-auto"></div>
            <p className="mt-4 text-muted">Loading projects...</p>
          </div>
        ) : !projects || projects.length === 0 ? (
          <div className="text-center py-16">
            <div className="mx-auto w-24 h-24 bg-card-muted rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-12 h-12 text-muted"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-fg mb-2">
              {searchQuery || statusFilter !== "all" ? "No projects found" : "No projects yet"}
            </h3>
            <p className="text-muted mb-6 max-w-sm mx-auto">
              {searchQuery || statusFilter !== "all"
                ? "Try adjusting your search or filter to find what you're looking for."
                : "Get started by creating your first website project."}
            </p>
            {!searchQuery && statusFilter === "all" && (
              <button
                onClick={() => router.push("/dashboard/new")}
                className="inline-flex items-center gap-2 px-6 py-3 bg-brand-gradient text-brand-fg font-medium rounded-full shadow-glow-sm hover:shadow-glow hover:-translate-y-0.5 active:translate-y-0 transition-all"
              >
                <Plus className="w-5 h-5" />
                Create Your First Project
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects?.map((project) => (
              <ProjectCard
                key={project.id}
                project={{
                  id: project.id,
                  name: project.name,
                  description: project.description || undefined,
                  html_content: "",
                  css_content: "",
                  js_content: "",
                  user_id: project.user_id,
                  created_at: project.created_at,
                  updated_at: project.updated_at,
                  is_published: project.published,
                  preview_url: project.deployment_url || undefined,
                  thumbnail_url: project.thumbnail_url || undefined,
                }}
                onDelete={handleDeleteProject}
                onDuplicate={handleDuplicateProject}
              />
            ))}
          </div>
        )}

        {/* Pagination - Show if we have projects */}
        {projects && projects.length > 0 && (
          <div className="mt-6">
            <Pagination
              currentPage={currentPage}
              totalItems={
                // Estimate total: if we got a full page, assume there might be more
                projects.length === itemsPerPage
                  ? currentPage * itemsPerPage + 1 // At least one more page
                  : currentPage * itemsPerPage - (itemsPerPage - projects.length) // Last page
              }
              itemsPerPage={itemsPerPage}
              onPageChange={setCurrentPage}
              onItemsPerPageChange={handleItemsPerPageChange}
            />
          </div>
        )}
      </main>
    </div>
  );
}
