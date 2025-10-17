"use client";

/**
 * DashboardPage.tsx
 *
 * This file contains the DashboardPage component, which is used to display the dashboard page.
 */


import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";  
import { TemplateCard } from "@/components/TemplateCard";
import { PromptInput } from "@/components/PromptInput";
import { useUnifiedGeneration } from "@/hooks/useUnifiedGeneration";

interface Template {
  id: string;
  name: string;
  description: string | null;
  category: string | null;
  preview_image: string | null;
  preview_url?: string | null;
  is_system_template: boolean;
}

const BUSINESS_CATEGORIES = [
  { value: "restaurant", label: "Restaurant & Food" },
  { value: "consultancy", label: "Consultancy & Services" },
  { value: "portfolio", label: "Portfolio & Creative" },
  { value: "retail", label: "Retail & E-commerce" },
  { value: "health", label: "Health & Fitness" },
  { value: "realestate", label: "Real Estate" },
  { value: "education", label: "Education & Training" },
  { value: "other", label: "Other" },
];

/**
 * Dashboard page - Protected route
 * Requires authentication to access
 */
export default function DashboardPage() {
  const router = useRouter();
  const { user, loading, signOut } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [userProfile, setUserProfile] = useState<{
    avatar_url?: string | null;
    first_name?: string | null;
    last_name?: string | null;
  } | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Website generation state
  const { generateWebsite, isGenerating, error, generatedProject } = useUnifiedGeneration();
  const [prompt, setPrompt] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [primaryColor, setPrimaryColor] = useState("#6366f1");
  const [showExamples, setShowExamples] = useState(false);

  // Templates state
  const [templates, setTemplates] = useState<Template[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(true);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/login");
    }
  }, [user, loading, router]);

  // Fetch user profile for avatar
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const profile = await api.users.getProfile();
        setUserProfile(profile);
      } catch (error) {
        console.error("Failed to fetch user profile:", error);
      }
    };

    if (user) {
      fetchProfile();
    }
  }, [user]);

  // Fetch templates on mount
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        setTemplatesLoading(true);
        // UNCOMMENT THIS WHEN TEMPLATES ARE READY
        // const data = await api.templates.list();
        // setTemplates(data);
        setTemplates([]);
      } catch (error) {
        console.error("Failed to fetch templates:", error);
        setTemplates([]);
      } finally {
        setTemplatesLoading(false);
      }
    };

    if (user) {
      fetchTemplates();
    }
  }, [user]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSignOut = async () => {
    await signOut();
    router.push("/auth/login");
  };

  const handleGenerate = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!prompt.trim()) return;

    const result = await generateWebsite(
      prompt.trim(),
      undefined, // projectName
      {
        primaryColor,
      }
    );

    if (result) {
      // Website generated successfully
      console.log("Website generated:", result);
      // Could navigate to the project or show success message
      setPrompt("");

      if (result.status === 'completed') {
        router.push(`/dashboard/projects/${result.project_id}`);
      }
      
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleGenerate();
    }
  };

  const handleTemplateSelect = (templateId: string) => {
    if (templateId === "blank") {
      // Handle blank template
      console.log("Start blank template");
      return;
    }
    // Navigate to template editor or preview
    console.log("Selected template:", templateId);
  };

  const getInitials = () => {
    if (userProfile?.first_name && userProfile?.last_name) {
      return `${userProfile.first_name[0]}${userProfile.last_name[0]}`.toUpperCase();
    }
    if (userProfile?.first_name) {
      return userProfile.first_name[0].toUpperCase();
    }
    if (user?.email) {
      return user.email[0].toUpperCase();
    }
    return "U";
  };

  const getDisplayName = () => {
    if (userProfile?.first_name && userProfile?.last_name) {
      return `${userProfile.first_name} ${userProfile.last_name}`;
    }
    if (userProfile?.first_name) {
      return userProfile.first_name;
    }
    return user?.email;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  // Limit to 5 templates for main dashboard
  const displayedTemplates = templates.slice(0, 5);

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                SiteSmith
              </h1>
            </div>

            <div className="flex items-center gap-4">
              {/* Browse Templates Button */}
              <button
                onClick={() => router.push("/dashboard/templates")}
                className="px-4 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-700 transition-colors"
              >
                Browse Templates
              </button>

              {/* User Avatar Dropdown */}
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  className="flex items-center space-x-3 hover:bg-gray-50 rounded-lg px-3 py-2 transition-colors"
                >
                  {/* Avatar */}
                  <div className="flex items-center space-x-3">
                    {userProfile?.avatar_url ? (
                      <img
                        src={userProfile.avatar_url}
                        alt="Profile"
                        className="w-10 h-10 rounded-full object-cover ring-2 ring-gray-200"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-semibold text-sm ring-2 ring-gray-200">
                        {getInitials()}
                      </div>
                    )}

                    {/* User Info */}
                    <div className="text-left hidden sm:block">
                      <p className="text-sm font-medium text-gray-900">
                        {getDisplayName()}
                      </p>
                      <p className="text-xs text-gray-500">{user.email}</p>
                    </div>
                  </div>

                  {/* Dropdown Arrow */}
                  <svg
                    className={`w-4 h-4 text-gray-500 transition-transform ${dropdownOpen ? "rotate-180" : ""
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

                {/* Dropdown Menu */}
                {dropdownOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                    {/* User Info in Dropdown (mobile) */}
                    <div className="px-4 py-3 border-b border-gray-100 sm:hidden">
                      <p className="text-sm font-medium text-gray-900">
                        {getDisplayName()}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">{user.email}</p>
                    </div>

                    {/* Profile Link */}
                    <button
                      onClick={() => {
                        router.push("/dashboard/profile");
                        setDropdownOpen(false);
                      }}
                      className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 flex items-center space-x-3 transition-colors"
                    >
                      <svg
                        className="w-5 h-5 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                        />
                      </svg>
                      <span>Profile</span>
                    </button>

                    {/* Logout Button */}
                    <button
                      onClick={() => {
                        handleSignOut();
                        setDropdownOpen(false);
                      }}
                      className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 flex items-center space-x-3 transition-colors"
                    >
                      <svg
                        className="w-5 h-5 text-red-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                        />
                      </svg>
                      <span>Sign out</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Create a new website with AI
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Simply describe your business or project, and our AI will generate a
            beautiful, professional website for you in minutes.
          </p>
        </div>

        {/* Prompt Input Section */}
        <div className="max-w-4xl mx-auto mb-12">
          <div className="relative">
            <div className="flex items-center gap-3 bg-white rounded-xl border-2 border-gray-200 focus-within:border-indigo-500 transition-colors shadow-sm">
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="e.g., 'A modern coffee shop in downtown Seattle'"
                className="flex-1 px-6 py-4 text-base text-gray-900 placeholder-gray-400 bg-transparent border-0 focus:outline-none focus:ring-0"
                maxLength={500}
                disabled={isGenerating}
              />
              <button
                onClick={handleGenerate}
                disabled={!prompt.trim() || isGenerating}
                className="mr-3 px-8 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors duration-200 whitespace-nowrap"
              >
                {isGenerating ? (
                  <span className="flex items-center gap-2">
                    <svg
                      className="animate-spin h-4 w-4"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Generating...
                  </span>
                ) : (
                  "Generate"
                )}
              </button>
            </div>
            <div className="absolute -bottom-6 right-0 text-xs text-gray-400">
              {prompt.length}/500
            </div>
          </div>
        </div>

        {/* Template Generation Options (Collapsible) */}
        {prompt.length > 0 && (
          <div className="max-w-4xl mx-auto mb-12">
            <button
              onClick={() => setShowExamples(!showExamples)}
              className="text-sm text-indigo-600 hover:text-indigo-700 font-medium mb-4"
            >
              {showExamples ? "Hide" : "Show"} advanced options
            </button>

            {showExamples && (
              <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
                {/* Business Category */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Business Category (Optional)
                  </label>
                  <select
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                  >
                    <option value="">Select a category...</option>
                    {BUSINESS_CATEGORIES.map((category) => (
                      <option key={category.value} value={category.value}>
                        {category.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Primary Color */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Primary Color (Optional)
                  </label>
                  <div className="flex items-center space-x-3">
                    <input
                      type="color"
                      value={primaryColor}
                      onChange={(e) => setPrimaryColor(e.target.value)}
                      className="h-12 w-20 rounded border border-gray-300 cursor-pointer"
                    />
                    <input
                      type="text"
                      value={primaryColor}
                      onChange={(e) => setPrimaryColor(e.target.value)}
                      className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      placeholder="#6366f1"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="max-w-4xl mx-auto mb-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <svg
                  className="h-5 w-5 text-red-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="ml-3 text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Success Display */}
        {generatedProject && generatedProject.status === 'completed' && (
          <div className="max-w-4xl mx-auto mb-8">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start">
                <svg
                  className="h-5 w-5 text-green-400 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-green-800">
                    Website Generated Successfully!
                  </h3>
                  <p className="mt-1 text-sm text-green-700">
                    Your website is ready to use.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Generating Display */}
        {generatedProject && generatedProject.status === 'generating' && (
          <div className="max-w-4xl mx-auto mb-8">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start">
                <svg
                  className="h-5 w-5 text-yellow-400 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800">
                    Website is being generated...
                  </h3>
                  <p className="mt-1 text-sm text-yellow-700">
                    Please wait while we generate your website. This may take a few minutes.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Divider */}
        {displayedTemplates ? (
          <div></div>
        ) : (
          <div className="relative mb-12">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200"></div>
            </div>
            <div className="relative flex justify-center">
              <span className="px-4 bg-gray-50 text-base text-gray-500 font-medium text-center">
                OR
                <br />
                start with a template
              </span>
            </div>
          </div>
        )}

        {/* Template Grid */}
        {/* COMMENTED OUT FOR NOW WHILE FOCUSING ON JUST UNIFIED GENERATION */}
        {templatesLoading ? (
          <div className="text-center py-12">
            {/* <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading templates...</p> */}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {/* Start Blank Option */}
            {/* <TemplateCard
              id="blank"
              name="Start Blank"
              onSelect={handleTemplateSelect}
              isBlank
            /> */}

            {/* Display up to 5 templates */}
            {/* {displayedTemplates.map((template) => (
              <TemplateCard
                key={template.id}
                id={template.id}
                name={template.name}
                description={template.description || undefined}
                category={template.category || undefined}
                previewImage={template.preview_image || undefined}
                isSystemTemplate={template.is_system_template}
                onSelect={handleTemplateSelect}
              />
            ))} */}
          </div>
        )}
      </main>
    </div>
  );
}
