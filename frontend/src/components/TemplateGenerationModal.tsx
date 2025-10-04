"use client";

/**
 * TemplateGenerationModal.tsx
 *
 * This file contains the TemplateGenerationModal component, which is used to generate templates using the useTemplateGeneration hook.
 * It provides a user interface for template generation, including a prompt input, example prompts, business category selector,
 * primary color picker, and a multi-stage UI (input → generating → preview).
 */


import { useState, useEffect } from "react";
import { useTemplateGeneration } from "@/hooks/useTemplateGeneration";
import { useRouter } from "next/navigation";

interface TemplateGenerationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const PROMPT_EXAMPLES = [
  "Modern restaurant with warm colors, menu showcase, and online ordering",
  "Professional consultancy with trust-building elements and service highlights",
  "Creative portfolio with large image galleries and minimalist design",
  "Local artisan shop with product showcase and WhatsApp ordering",
  "Fitness studio with class schedules and membership options",
  "Real estate agency with property listings and contact forms",
];

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

export default function TemplateGenerationModal({
  isOpen,
  onClose,
}: TemplateGenerationModalProps) {
  const router = useRouter();
  const { generateTemplate, isGenerating, error, generatedTemplate, clearError } =
    useTemplateGeneration();

  const [prompt, setPrompt] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [primaryColor, setPrimaryColor] = useState("#6366f1");
  const [showExamples, setShowExamples] = useState(false);
  const [currentStage, setCurrentStage] = useState<
    "input" | "generating" | "preview" | "success"
  >("input");

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setCurrentStage("input");
      setPrompt("");
      setSelectedCategory("");
      setPrimaryColor("#6366f1");
      clearError();
    }
  }, [isOpen, clearError]);

  // Update stage based on generation status
  useEffect(() => {
    if (isGenerating) {
      setCurrentStage("generating");
    } else if (generatedTemplate) {
      setCurrentStage("preview");
    }
  }, [isGenerating, generatedTemplate]);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      return;
    }

    const result = await generateTemplate({
      prompt: prompt.trim(),
      style_preferences: {
        primaryColor,
      },
    });

    if (result) {
      setCurrentStage("preview");
    }
  };

  const handleUseTemplate = () => {
    if (generatedTemplate) {
      // Navigate to the dashboard with the new template
      router.push(`/dashboard/new?template=${generatedTemplate.id}`);
      onClose();
    }
  };

  const handleRegenerateWithPrompt = (examplePrompt: string) => {
    setPrompt(examplePrompt);
    setShowExamples(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative w-full max-w-3xl bg-white rounded-xl shadow-2xl transform transition-all">
          {/* Header */}
          <div className="border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  Generate Website Template
                </h2>
                <p className="mt-1 text-sm text-gray-500">
                  Describe your website and let AI create a template for you
                </p>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-6">
            {/* Input Stage */}
            {currentStage === "input" && (
              <div className="space-y-6">
                {/* Prompt Input */}
                <div>
                  <label
                    htmlFor="prompt"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Describe Your Website
                  </label>
                  <textarea
                    id="prompt"
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                    placeholder="e.g., Modern restaurant with warm colors, menu showcase, and online ordering capability..."
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                  />
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-xs text-gray-500">
                      {prompt.length}/1000 characters
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowExamples(!showExamples)}
                      className="text-xs text-indigo-600 hover:text-indigo-700 font-medium"
                    >
                      {showExamples ? "Hide" : "Show"} examples
                    </button>
                  </div>
                </div>

                {/* Examples */}
                {showExamples && (
                  <div className="bg-indigo-50 rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-700 mb-3">
                      Example Prompts:
                    </p>
                    <div className="space-y-2">
                      {PROMPT_EXAMPLES.map((example, index) => (
                        <button
                          key={index}
                          onClick={() => handleRegenerateWithPrompt(example)}
                          className="w-full text-left text-sm text-gray-600 hover:text-indigo-600 hover:bg-white px-3 py-2 rounded transition-colors"
                        >
                          "{example}"
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Business Category */}
                <div>
                  <label
                    htmlFor="category"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Business Category (Optional)
                  </label>
                  <select
                    id="category"
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

                {/* Style Preferences */}
                <div>
                  <label
                    htmlFor="primaryColor"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Primary Color (Optional)
                  </label>
                  <div className="flex items-center space-x-3">
                    <input
                      type="color"
                      id="primaryColor"
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

                {/* Error Display */}
                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex">
                      <div className="flex-shrink-0">
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
                      </div>
                      <div className="ml-3">
                        <p className="text-sm text-red-700">{error}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Generating Stage */}
            {currentStage === "generating" && (
              <div className="py-12">
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-indigo-200 border-t-indigo-600 mb-6" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Generating Your Template...
                  </h3>
                  <div className="space-y-3 max-w-md mx-auto">
                    <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
                      <div className="w-2 h-2 bg-indigo-600 rounded-full animate-pulse" />
                      <span>Analyzing business requirements</span>
                    </div>
                    <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
                      <div className="w-2 h-2 bg-indigo-600 rounded-full animate-pulse delay-75" />
                      <span>Selecting appropriate components</span>
                    </div>
                    <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
                      <div className="w-2 h-2 bg-indigo-600 rounded-full animate-pulse delay-150" />
                      <span>Customizing styles and layout</span>
                    </div>
                    <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
                      <div className="w-2 h-2 bg-indigo-600 rounded-full animate-pulse delay-300" />
                      <span>Generating preview</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Preview Stage */}
            {currentStage === "preview" && generatedTemplate && (
              <div className="space-y-6">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg
                        className="h-5 w-5 text-green-400"
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
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-green-800">
                        Template Generated Successfully!
                      </h3>
                      <p className="mt-1 text-sm text-green-700">
                        Your template "{generatedTemplate.name}" is ready to use.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Template Info */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">
                    {generatedTemplate.name}
                  </h3>
                  <p className="text-sm text-gray-600 mb-4">
                    {generatedTemplate.description}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                      {generatedTemplate.category}
                    </span>
                    {generatedTemplate.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                  <div className="mt-4 text-sm text-gray-500">
                    <span className="font-medium">
                      {generatedTemplate.sections_config.length}
                    </span>{" "}
                    sections included
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 rounded-b-xl">
            <div className="flex justify-end space-x-3">
              {currentStage === "input" && (
                <>
                  <button
                    onClick={onClose}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleGenerate}
                    disabled={!prompt.trim() || isGenerating}
                    className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                  >
                    Generate Template
                  </button>
                </>
              )}

              {currentStage === "preview" && (
                <>
                  <button
                    onClick={() => {
                      setCurrentStage("input");
                      setPrompt("");
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Generate Another
                  </button>
                  <button
                    onClick={handleUseTemplate}
                    className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                  >
                    Use This Template
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

