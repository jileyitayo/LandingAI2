'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface SubdomainInputProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
  onValidationChange?: (isValid: boolean) => void;
}

export default function SubdomainInput({
  value,
  onChange,
  error: externalError,
  onValidationChange,
}: SubdomainInputProps) {
  const [checking, setChecking] = useState(false);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [internalError, setInternalError] = useState<string>('');

  const error = externalError || internalError;

  useEffect(() => {
    const checkAvailability = async () => {
      if (!value || value.length < 3) {
        setAvailable(null);
        setSuggestions([]);
        setInternalError('');
        onValidationChange?.(false);
        return;
      }

      // Validate format
      const validFormat = /^[a-z0-9-]{3,20}$/.test(value.toLowerCase());
      if (!validFormat) {
        setAvailable(false);
        setInternalError('Only lowercase letters, numbers, and hyphens allowed');
        setSuggestions([]);
        onValidationChange?.(false);
        return;
      }

      setChecking(true);
      setInternalError('');

      try {
        const result = await api.projects.checkSubdomain(value.toLowerCase());
        setAvailable(result.available);
        setSuggestions(result.suggestions || []);
        onValidationChange?.(result.available);
      } catch (err: any) {
        setInternalError(err.message || 'Failed to check availability');
        setAvailable(false);
        onValidationChange?.(false);
      } finally {
        setChecking(false);
      }
    };

    const timeoutId = setTimeout(checkAvailability, 500);
    return () => clearTimeout(timeoutId);
  }, [value, onValidationChange]);

  return (
    <div className="space-y-2">
      <label htmlFor="subdomain" className="block text-sm font-medium text-gray-700">
        Subdomain
      </label>
      <div className="mt-1 flex rounded-md shadow-sm">
        <input
          type="text"
          id="subdomain"
          value={value}
          onChange={(e) => onChange(e.target.value.toLowerCase())}
          placeholder="mysite"
          className={`flex-1 min-w-0 block w-full px-3 py-2 rounded-l-md border ${
            error
              ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
              : available === true
              ? 'border-green-300 focus:ring-green-500 focus:border-green-500'
              : 'border-gray-300 focus:ring-indigo-500 focus:border-indigo-500'
          } focus:outline-none focus:ring-2 sm:text-sm`}
        />
        <span className="inline-flex items-center px-3 rounded-r-md border border-l-0 border-gray-300 bg-gray-50 text-gray-500 sm:text-sm">
          .sitesmith.app
        </span>
      </div>

      {/* Status indicator */}
      {value.length >= 3 && (
        <div className="flex items-center space-x-2 text-sm">
          {checking ? (
            <span className="text-gray-500">Checking availability...</span>
          ) : error ? (
            <span className="text-red-600">{error}</span>
          ) : available === true ? (
            <span className="text-green-600 flex items-center">
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              Available
            </span>
          ) : available === false ? (
            <span className="text-red-600 flex items-center">
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              Not available
            </span>
          ) : null}
        </div>
      )}

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="text-sm">
          <p className="text-gray-600 mb-1">Try these instead:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => onChange(suggestion)}
                className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded border border-gray-300 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      <p className="text-xs text-gray-500">
        Your site will be available at: {value || 'mysite'}.sitesmith.app
      </p>
    </div>
  );
}

