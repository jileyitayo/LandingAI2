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
import { useActiveGenerations } from "@/contexts/GenerationContext";
import DashboardHeader from "@/components/DashboardHeader";
import GenerationStatus from "@/components/GenerationStatus";
import AttachmentButton, { type Attachment } from "@/components/AttachmentButton";
import ClarificationCard from "@/components/ClarificationCard";

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
  const { generateWebsite, resume, isGenerating, error, generatedProject, clarification, clearClarification } = useUnifiedGeneration();
  const generations = useActiveGenerations();
  const [prompt, setPrompt] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [primaryColor, setPrimaryColor] = useState("#7c3aed");
  const [attachments, setAttachments] = useState<Attachment[]>([]);

  // Templates state
  const [templates, setTemplates] = useState<Template[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(true);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/login");
    }
  }, [user, loading, router]);

  // Resume tracking a generation after refresh/navigation: the project id is
  // kept in the URL (?project_id=...) so remounting re-attaches the polling
  useEffect(() => {
    if (!user) return;
    const projectId = new URLSearchParams(window.location.search).get("project_id");
    if (projectId) {
      resume(projectId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  const handleGenerate = async (
    e?: React.FormEvent,
    options?: { skipClarification?: boolean; clarificationResponse?: string }
  ) => {
    e?.preventDefault();
    if (prompt.trim().length < 20) return;

    const result = await generateWebsite(
      prompt.trim(),
      undefined, // projectName
      {
        primaryColor,
      },
      attachments.map((a) => ({
        media_id: a.id,
        url: a.url,
        media_type: a.mediaType,
      })),
      options
    );

    // On a clarification response the prompt/attachments must survive so the
    // user can answer and resubmit — only clear once generation really starts.
    if (result?.project_id) {
      setPrompt("");
      setAttachments([]);

      // Keep the project id in the URL so a refresh/navigation re-attaches,
      // and register with the dashboard-wide tracker (banner + cards)
      window.history.replaceState(null, "", `?project_id=${result.project_id}`);
      generations?.track(result.project_id);
    }
  };

  // Resubmit after the user answers (or dismisses) the pre-flight question.
  // skipClarification guarantees max one clarification round.
  const handleClarificationAnswer = (answer?: string) => {
    clearClarification();
    handleGenerate(undefined, { skipClarification: true, clarificationResponse: answer });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
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

  // Limit to 5 templates for main dashboard
  const displayedTemplates = templates.slice(0, 5);

  return (
    <div className="min-h-screen bg-surface">
      <DashboardHeader />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="font-display text-5xl font-bold text-fg mb-4">
            Create a new website with AI
          </h1>
          <p className="text-lg text-muted max-w-2xl mx-auto">
            Simply describe your business or project, and our AI will generate a
            beautiful, professional website for you in minutes.
          </p>
        </div>

        {/* Prompt Input Section */}
        <div className="max-w-4xl mx-auto mb-12">
          <div className="relative">
            <div className="flex items-end gap-3 bg-card rounded-2xl border border-border focus-within:border-brand focus-within:ring-2 focus-within:ring-brand/40 focus-within:shadow-glow-sm transition shadow-card px-4 py-3">
              <div className="pb-0.5">
                <AttachmentButton
                  attachments={attachments}
                  onAttachmentsChange={setAttachments}
                  disabled={isGenerating}
                />
              </div>
              <textarea
                value={prompt}
                onChange={(e) => {
                  setPrompt(e.target.value);
                  const el = e.target;
                  el.style.height = "auto";
                  el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
                }}
                onKeyDown={handleKeyPress}
                placeholder="e.g., 'A modern coffee shop in downtown Seattle'"
                rows={1}
                className="flex-1 px-2 py-2 text-base text-fg placeholder:text-muted bg-transparent border-0 focus:outline-none focus:ring-0 resize-none"
                maxLength={1000}
                disabled={isGenerating}
              />
              <button
                onClick={handleGenerate}
                disabled={prompt.trim().length < 20 || isGenerating}
                className="mr-3 px-8 py-3 bg-brand-gradient text-brand-fg font-medium rounded-full shadow-glow-sm hover:shadow-glow disabled:opacity-50 disabled:shadow-none disabled:cursor-not-allowed transition-all duration-200 whitespace-nowrap"
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
            <div className="absolute -bottom-6 right-0 text-xs">
              <span className={prompt.trim().length < 20 ? "text-muted" : "text-muted/70"}>
                {prompt.length}/1000 {prompt.trim().length < 20 && `(min. 20 characters)`}
              </span>
            </div>
          </div>
        </div>

        {/* Pre-flight clarification (response-driven: only when the backend asks) */}
        {clarification && (
          <ClarificationCard
            clarification={clarification}
            attachments={attachments}
            onAttachmentsChange={setAttachments}
            onAnswer={handleClarificationAnswer}
            onGenerateAnyway={() => handleClarificationAnswer(undefined)}
            disabled={isGenerating}
          />
        )}

        {/* Error Display */}
        {error && (
          <div className="max-w-4xl mx-auto mb-8">
            <div className="bg-red-50 border border-red-200 dark:bg-red-500/10 dark:border-red-500/30 rounded-lg p-4">
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
                <p className="ml-3 text-sm text-red-700 dark:text-red-400">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Success Display */}
        {generatedProject && generatedProject.status === 'completed' && (
          <div className="max-w-4xl mx-auto mb-8">
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-500/10 dark:to-emerald-500/10 border-2 border-green-300 dark:border-green-500/40 rounded-2xl p-8 shadow-lg">
              <div className="text-center">
                {/* Celebration Icon */}
                <div className="mb-4 flex justify-center">
                  <div className="relative">
                    <div className="absolute inset-0 bg-green-400 rounded-full blur-xl opacity-30 animate-pulse"></div>
                    <div className="relative bg-gradient-to-br from-green-400 to-emerald-500 rounded-full p-4 shadow-lg">
                      <svg
                        className="h-12 w-12 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2.5}
                          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                    </div>
                  </div>
                </div>
                
                {/* Congratulatory Message */}
                <h3 className="font-display text-3xl font-bold text-green-800 dark:text-green-300 mb-2">
                  🎉 Congratulations! 🎉
                </h3>
                <p className="text-xl text-green-700 dark:text-green-300/90 font-semibold mb-1">
                  Your website has been generated successfully!
                </p>
                <p className="text-base text-green-600 dark:text-green-400/80 mb-6">
                  Your beautiful, professional website is ready to use and customize.
                </p>
                
                {/* Action Button */}
                <button
                  onClick={() => router.push(`/dashboard/projects/${generatedProject.project_id}`)}
                  className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white text-lg font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
                >
                  <span>View Your Website</span>
                  <svg
                    className="ml-3 w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2.5}
                      d="M13 7l5 5m0 0l-5 5m5-5H6"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Generating Display */}
        {generatedProject && generatedProject.status === 'generating' && (
          <GenerationStatus
            status={generatedProject.status}
            progress={generatedProject.progress}
            stage={generatedProject.stage}
            stageMessage={generatedProject.stage_message}
            message={generatedProject.message}
          />
        )}

        {/* Divider */}
        {displayedTemplates ? (
          <div></div>
        ) : (
          <div className="relative mb-12">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border"></div>
            </div>
            <div className="relative flex justify-center">
              <span className="px-4 bg-surface text-base text-muted font-medium text-center">
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
            {/* <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand mx-auto"></div>
            <p className="mt-4 text-muted">Loading templates...</p> */}
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
