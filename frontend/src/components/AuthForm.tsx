"use client";

import { ReactNode, forwardRef } from "react";
import Link from "next/link";

interface AuthFormProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
  onSubmit: (e: React.FormEvent) => void;
  error?: string | null;
}

/**
 * Reusable authentication form wrapper component
 * Provides consistent styling and layout for all auth forms
 */
export function AuthForm({
  title,
  subtitle,
  children,
  footer,
  onSubmit,
  error,
}: AuthFormProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50 px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-block">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              SiteSmith
            </h1>
          </Link>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          {/* Header */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">{title}</h2>
            {subtitle && <p className="text-gray-600 text-sm">{subtitle}</p>}
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Form Content */}
          <form onSubmit={onSubmit} className="space-y-4">
            {children}
          </form>

          {/* Footer */}
          {footer && (
            <div className="mt-6 pt-6 border-t border-gray-200">{footer}</div>
          )}
        </div>

        {/* Additional Links */}
        <div className="text-center mt-6">
          <p className="text-sm text-gray-600">
            By continuing, you agree to our{" "}
            <Link
              href="/terms"
              className="text-indigo-600 hover:text-indigo-700"
            >
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link
              href="/privacy"
              className="text-indigo-600 hover:text-indigo-700"
            >
              Privacy Policy
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

interface InputFieldProps {
  label: string;
  type: string;
  name: string;
  placeholder?: string;
  required?: boolean;
  autoComplete?: string;
  error?: string;
  disabled?: boolean;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
}

/**
 * Styled input field component for auth forms
 */
export const InputField = forwardRef<HTMLInputElement, InputFieldProps>(
  (
    {
      label,
      type,
      name,
      placeholder,
      required = false,
      autoComplete,
      error,
      disabled = false,
      value,
      onChange,
      onBlur,
    }: InputFieldProps,
    ref
  ) => {
    return (
      <div>
        <label
          htmlFor={name}
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        <input
          id={name}
          name={name}
          type={type}
          placeholder={placeholder}
          required={required}
          autoComplete={autoComplete}
          disabled={disabled}
          value={value}
          onChange={onChange}
          onBlur={onBlur}
          ref={ref}
          className={`
            w-full px-4 py-2.5 rounded-lg border transition-colors
            focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
            disabled:bg-gray-100 disabled:cursor-not-allowed
            ${
              error
                ? "border-red-300 bg-red-50"
                : "border-gray-300 bg-white hover:border-gray-400"
            }
          `}
        />
        {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
      </div>
    );
  }
);

InputField.displayName = "InputField";

interface SubmitButtonProps {
  children: ReactNode;
  isLoading?: boolean;
  disabled?: boolean;
}

/**
 * Styled submit button component for auth forms
 */
export function SubmitButton({
  children,
  isLoading = false,
  disabled = false,
}: SubmitButtonProps) {
  return (
    <button
      type="submit"
      disabled={disabled || isLoading}
      className={`
        w-full px-4 py-2.5 rounded-lg font-medium text-white
        bg-gradient-to-r from-indigo-600 to-purple-600
        hover:from-indigo-700 hover:to-purple-700
        focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed
        transition-all duration-200
        ${isLoading ? "cursor-wait" : ""}
      `}
    >
      {isLoading ? (
        <span className="flex items-center justify-center">
          <svg
            className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          Loading...
        </span>
      ) : (
        children
      )}
    </button>
  );
}
