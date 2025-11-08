"use client";

/**
 * DashboardPage.tsx
 *
 * This file contains the DashboardPage component, which is used to display the dashboard page.
 */


import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { TemplateCard } from "@/components/TemplateCard";
import { useUnifiedGeneration } from "@/hooks/useUnifiedGeneration";
import DashboardHeader from "@/components/DashboardHeader";

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
  const { user, loading } = useAuth();

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
      // Could navigate to the project or show success message
      setPrompt("");

      // if (result.status === 'completed') {
      //   router.push(`/dashboard/projects/${result.project_id}`);
      // }
      
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
      // console.log("Start blank template");
      return;
    }
    // Navigate to template editor or preview
    // console.log("Selected template:", templateId);
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
      <DashboardHeader />

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
                <div className="ml-3 flex-1">
                  <h3 className="text-sm font-medium text-green-800">
                    Website Generated Successfully!
                  </h3>
                  <p className="mt-1 text-sm text-green-700">
                    Your website is ready to use.
                  </p>
                  <button
                    onClick={() => router.push(`/dashboard/projects/${generatedProject.project_id}`)}
                    className="mt-3 inline-flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors duration-200"
                  >
                    View Project
                    <svg
                      className="ml-2 w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 7l5 5m0 0l-5 5m5-5H6"
                      />
                    </svg>
                  </button>
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
