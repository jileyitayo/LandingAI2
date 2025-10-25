"use client";
/**
 * useTemplateGeneration.ts
 *
 * This file provides a custom React hook for managing website generation via API calls.
 *
 * Main responsibilities:
 * - Exposes a function to initiate website generation based on user input (prompt and style preferences).
 * - Handles polling and status checking for the generation process.
 * - Manages local state for loading, errors, and the generated project data.
 * - Provides a mechanism to clear errors.
 *
 * The hook is intended for use in frontend components that need to trigger and monitor website generation.
 */

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { toast } from "sonner";

export const useUnifiedGeneration = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedProject, setGeneratedProject] = useState<any>(null);

  const generateWebsite = async (prompt: string, projectName?: string, stylePreferences?: any) => {
    setIsGenerating(true);
    setError(null);

    try {
      const result = await api.generation.generateWebsite({
        prompt,
        project_name: projectName,
        style_preferences: stylePreferences
      });

      setGeneratedProject(result);

      // Start polling for status
      pollStatus(result.project_id);

      return result;
    } catch (err) {
      if (err instanceof ApiError) {
        // Handle rate limit errors specifically
        if (err.status === 429) {
          const limitType = err.detail?.['X-RateLimit-Type'] || 'unknown';
          const tier = err.detail?.['X-RateLimit-Tier'] || 'free';
          const retryAfter = err.detail?.['Retry-After'] || 'soon';

          const message = limitType === 'per_minute'
            ? `Rate limit exceeded: Too many requests per minute. Please wait ${retryAfter} seconds before trying again.`
            : `Daily generation limit reached. Your ${tier} tier limit has been exceeded. Please upgrade your plan or try again tomorrow.`;

          toast.error("Rate Limit Exceeded", {
            description: message,
            duration: 6000,
          });
          setError(message);
        } else {
          toast.error("Generation Failed", {
            description: err.message,
            duration: 5000,
          });
          setError(err.message);
        }
      } else {
        const errorMessage = err instanceof Error ? err.message : 'Generation failed';
        toast.error("Generation Failed", {
          description: errorMessage,
          duration: 5000,
        });
        setError(errorMessage);
      }
      throw err;
    }
    // finally {
    //   setIsGenerating(false);
    // }
  };

  const pollStatus = async (projectId: string) => {
    const maxAttempts = 30; // 5 minutes with 10-second intervals
    let attempts = 0;

    const poll = async () => {
      try {
        const status = await api.generation.getStatus(projectId);
        
        if (status.status === 'completed') {
          setGeneratedProject((prev: any) => prev ? { ...prev, status: 'completed' } : { status: 'completed' });
          setIsGenerating(false);
          return;
        } else if (status.status === 'failed') {
          setError(status.error || 'Generation failed');
          setIsGenerating(false);
          return;
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 15000); // Poll every 10 seconds
        } else {
          setError('Generation timed out');
          setIsGenerating(false);
        }
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError('Failed to check generation status');
        }
        setIsGenerating(false);
      }
    };

    poll();
  };

  return {
    generateWebsite,
    isGenerating,
    error,
    generatedProject,
    clearError: () => setError(null)
  };
};