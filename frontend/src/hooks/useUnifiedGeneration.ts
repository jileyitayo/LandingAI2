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

  const generateWebsite = async (
    prompt: string,
    projectName?: string,
    stylePreferences?: any,
    attachments?: Array<{ media_id: string; url: string; media_type?: string }>
  ) => {
    setIsGenerating(true);
    setError(null);

    try {
      const result = await api.generation.generateWebsite({
        prompt,
        project_name: projectName,
        style_preferences: stylePreferences,
        attachments,
      });

      // console.log('[Generation] Initial response:', result);

      // Set initial state with default progress values
      setGeneratedProject({
        ...result,
        progress: 0,
        stage: 'analyzing',
        stage_message: null,
        message: result.message || 'Starting generation...',
      });

      // Start polling for status immediately
      // console.log('[Generation] Starting polling for project:', result.project_id);
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
          // Extract validation error message if available
          const errorMessage = err.getValidationMessage();
          toast.error("Generation Failed", {
            description: errorMessage,
            duration: 5000,
          });
          setError(errorMessage);
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
    const maxAttempts = 300; // 6 minutes with 3-second intervals (increased from 30 attempts)
    let attempts = 0;

    const poll = async () => {
      try {
        // console.log(`[Polling] Attempt ${attempts + 1}/${maxAttempts} for project ${projectId}`);
        const status = await api.generation.getStatus(projectId);

        // console.log('[Polling] Received status:', {
        //   status: status.status,
        //   progress: status.progress,
        //   stage: status.stage,
        //   stage_message: status.stage_message,
        // });

        // Update generatedProject with full status including progress and stage
        setGeneratedProject((prev: any) => {
          const updated = {
            ...prev,
            status: status.status,
            progress: status.progress ?? prev.progress ?? 0,
            stage: status.stage ?? prev.stage,
            stage_message: status.stage_message ?? prev.stage_message,
            message: status.message ?? prev.message,
            error: status.error,
          };
          // console.log('[Polling] Updated state:', updated);
          return updated;
        });

        if (status.status === 'completed') {
          // console.log('[Polling] Generation completed!');
          setIsGenerating(false);
          return;
        } else if (status.status === 'failed') {
          // console.log('[Polling] Generation failed:', status.error);
          setError(status.error || 'Generation failed');
          setIsGenerating(false);
          return;
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 6000); // Poll every 3 seconds for real-time feel
        } else {
          // console.log('[Polling] Timed out after max attempts');
          setError('Generation timed out');
          setIsGenerating(false);
        }
      } catch (err) {
        // console.error('[Polling] Error:', err);
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError('Failed to check generation status');
        }
        setIsGenerating(false);
      }
    };

    // Start polling immediately
    poll();
  };

  /**
   * Re-attach to a generation already running server-side (e.g. after the
   * user navigated away and came back, or refreshed). Safe to call for a
   * completed/failed project — the first poll settles the state.
   */
  const resume = (projectId: string) => {
    setIsGenerating(true);
    setError(null);
    setGeneratedProject({
      project_id: projectId,
      status: 'generating',
      progress: 0,
      stage: null,
      stage_message: null,
      message: 'Reconnecting to your generation…',
    });
    pollStatus(projectId);
  };

  return {
    generateWebsite,
    resume,
    isGenerating,
    error,
    generatedProject,
    clearError: () => setError(null)
  };
};