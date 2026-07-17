"use client";

/**
 * ClarificationCard.tsx
 *
 * Pre-flight clarification card for the generation page. Rendered when the
 * backend returns status "needs_clarification" instead of starting a
 * generation (e.g. a referenced website couldn't be read, or the prompt
 * mentions an asset like "my logo" with nothing attached). Purely
 * response-driven: it never renders unless the backend asks.
 */

import { useState } from "react";
import AttachmentButton, { type Attachment } from "@/components/AttachmentButton";
import type { GenerationClarification } from "@/hooks/useUnifiedGeneration";

interface ClarificationCardProps {
  clarification: GenerationClarification;
  attachments: Attachment[];
  onAttachmentsChange: (attachments: Attachment[]) => void;
  onAnswer: (answer?: string) => void;
  onGenerateAnyway: () => void;
  disabled?: boolean;
}

export default function ClarificationCard({
  clarification,
  attachments,
  onAttachmentsChange,
  onAnswer,
  onGenerateAnyway,
  disabled = false,
}: ClarificationCardProps) {
  const [answer, setAnswer] = useState("");

  const hasInput = answer.trim().length > 0 || attachments.length > 0;

  return (
    <div className="max-w-4xl mx-auto mb-8">
      <div className="bg-brand/5 border border-brand/25 rounded-2xl p-6 shadow-sm">
        <div className="flex gap-3">
          <svg
            className="h-6 w-6 text-brand flex-shrink-0 mt-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-fg mb-1">
              Quick question before we generate
            </h3>
            <p className="text-sm text-fg/80 mb-4">{clarification.question}</p>

            <div className="flex items-end gap-2 bg-card rounded-xl border border-brand/25 px-3 py-2 mb-4">
              {clarification.wants_attachment && (
                <div className="pb-0.5">
                  <AttachmentButton
                    attachments={attachments}
                    onAttachmentsChange={onAttachmentsChange}
                    disabled={disabled}
                  />
                </div>
              )}
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder={
                  clarification.wants_attachment
                    ? "Attach a screenshot and/or describe it here…"
                    : "Type your answer…"
                }
                rows={2}
                maxLength={1000}
                disabled={disabled}
                className="flex-1 px-1 py-1 text-sm text-fg placeholder:text-muted bg-transparent border-0 focus:outline-none focus:ring-0 resize-none"
              />
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => onAnswer(answer.trim() || undefined)}
                disabled={disabled || !hasInput}
                className="px-5 py-2 bg-brand-gradient text-brand-fg text-sm font-medium rounded-full shadow-glow-sm hover:shadow-glow disabled:opacity-50 disabled:shadow-none disabled:cursor-not-allowed transition-all"
              >
                Answer & generate
              </button>
              <button
                onClick={onGenerateAnyway}
                disabled={disabled}
                className="px-5 py-2 bg-card text-brand text-sm font-medium rounded-full border border-brand/30 hover:bg-brand/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Generate anyway
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
