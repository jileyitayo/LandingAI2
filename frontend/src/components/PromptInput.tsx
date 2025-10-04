"use client";

/**
 * PromptInput.tsx
 *
 * This file contains the PromptInput component, which is used to display a prompt input in the template generation modal.
 */


import { useState } from "react";

interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
  onGenerate: () => void;
  isGenerating?: boolean;
  maxLength?: number;
}

const PROMPT_EXAMPLES = [
  "A landing page for a yoga studio with calming colors",
  "A portfolio website for a photographer with gallery",
  "A restaurant website with menu and reservations",
  "A modern business template with blue tones and professional layout",
  "A local artisan shop with product showcase",
];

export function PromptInput({
  value,
  onChange,
  onGenerate,
  isGenerating = false,
  maxLength = 500,
}: PromptInputProps) {
  const [showExamples, setShowExamples] = useState(false);

  const handleExampleClick = (example: string) => {
    onChange(example);
    setShowExamples(false);
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4">
      {/* Input Container */}
      <div className="relative">
        <div className="flex items-center gap-3 bg-white rounded-xl border-2 border-gray-200 focus-within:border-primary-500 transition-colors shadow-sm">
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => setShowExamples(true)}
            placeholder="e.g., 'A modern coffee shop in downtown Seattle'"
            className="flex-1 px-6 py-4 text-base text-gray-900 placeholder-gray-400 bg-transparent border-0 focus:outline-none focus:ring-0"
            maxLength={maxLength}
            disabled={isGenerating}
          />
          <button
            onClick={onGenerate}
            disabled={!value.trim() || isGenerating}
            className="mr-3 px-8 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors duration-200 whitespace-nowrap"
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

        {/* Character Count */}
        <div className="absolute -bottom-6 right-0 text-xs text-gray-400">
          {value.length}/{maxLength}
        </div>
      </div>

      {/* Examples Dropdown */}
      {showExamples && value.length === 0 && (
        <div className="relative z-10">
          <div className="absolute top-0 left-0 right-0 bg-white rounded-lg border border-gray-200 shadow-lg py-2">
            <div className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
              Try these examples
            </div>
            {PROMPT_EXAMPLES.map((example, index) => (
              <button
                key={index}
                onClick={() => handleExampleClick(example)}
                className="w-full px-4 py-3 text-left text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

