"use client";
/**
 * useTemplateGeneration.ts
 *
 * This file provides a custom React hook, `useTemplateGeneration`, for managing the process of generating templates via API calls.
 * 
 * Main responsibilities:
 * - Exposes a function to initiate template generation based on user input (prompt and style preferences).
 * - Handles polling and status checking for the template generation process.
 * - Manages local state for loading, errors, and the generated template data.
 * - Provides a mechanism to clear errors.
 * 
 * The hook is intended for use in frontend components that need to trigger and monitor template generation, 
 * such as template builders or onboarding flows.
 */


import { useState, useCallback } from "react";
import { api, ApiError } from "@/lib/api";

interface GenerateTemplateParams {
  prompt: string;
  style_preferences?: {
    primaryColor?: string;
    secondaryColor?: string;
    fontFamily?: string;
  };
}

interface Template {
  id: string;
  name: string;
  description: string;
  sections_config: Array<Record<string, any>>;
  style_config: Record<string, any>;
  content_schema: Record<string, any>;
  preview_html: string | null;
  preview_url: string | null;
  category: string;
  tags: string[];
  is_public: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string | null;
}

interface UseTemplateGenerationReturn {
  generateTemplate: (params: GenerateTemplateParams) => Promise<Template | null>;
  checkStatus: (templateId: string) => Promise<"completed" | "failed" | "pending">;
  isGenerating: boolean;
  error: string | null;
  generatedTemplate: Template | null;
  clearError: () => void;
}

/**
 * Custom hook for template generation
 * Handles API calls, polling, and state management for template generation
 */
export function useTemplateGeneration(): UseTemplateGenerationReturn {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedTemplate, setGeneratedTemplate] = useState<Template | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const generateTemplate = useCallback(async (params: GenerateTemplateParams): Promise<Template | null> => {
    setIsGenerating(true);
    setError(null);
    setGeneratedTemplate(null);

    try {
      const result = await api.templates.generate({
        prompt: params.prompt,
        style_preferences: params.style_preferences,
      });

      setGeneratedTemplate(result);
      return result;
    } catch (err) {
      if (err instanceof ApiError) {
        // Handle rate limiting
        if (err.status === 429) {
          setError("Rate limit exceeded. You can generate up to 3 templates per hour. Please try again later.");
        } 
        // Handle bad request
        else if (err.status === 400) {
          setError(err.message || "Invalid request. Please check your prompt and try again.");
        }
        // Handle server error
        else if (err.status >= 500) {
          setError("Server error. Please try again later.");
        }
        // Generic error
        else {
          setError(err.message || "Failed to generate template. Please try again.");
        }
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
      return null;
    } finally {
      setIsGenerating(false);
    }
  }, []);

  const checkStatus = useCallback(async (templateId: string): Promise<"completed" | "failed" | "pending"> => {
    try {
      const result = await api.templates.getStatus(templateId);
      
      if (result.status === "completed") {
        return "completed";
      } else if (result.status === "failed") {
        setError(result.error || "Template generation failed");
        return "failed";
      } else {
        return "pending";
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to check status");
      }
      return "failed";
    }
  }, []);

  return {
    generateTemplate,
    checkStatus,
    isGenerating,
    error,
    generatedTemplate,
    clearError,
  };
}

