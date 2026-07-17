"use client";

import { ReactNode, forwardRef } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

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
    <div className="relative min-h-screen flex items-center justify-center bg-surface px-4 py-12 overflow-hidden">
      {/* Ambient brand glow */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-48 left-1/2 -translate-x-1/2 h-[28rem] w-[40rem] rounded-full bg-brand/10 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-56 right-0 h-[24rem] w-[32rem] rounded-full bg-brand-2/10 blur-3xl"
      />

      <div className="relative w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-block">
            <h1 className="font-display text-3xl font-bold bg-brand-gradient bg-clip-text text-transparent">
              SiteSmith
            </h1>
          </Link>
        </div>

        {/* Form Card */}
        <div className="card p-8">
          {/* Header */}
          <div className="mb-6">
            <h2 className="font-display text-2xl font-semibold text-fg mb-2">
              {title}
            </h2>
            {subtitle && <p className="text-muted text-sm">{subtitle}</p>}
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 dark:bg-red-500/10 dark:border-red-500/30">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          {/* Form Content */}
          <form onSubmit={onSubmit} className="space-y-4">
            {children}
          </form>

          {/* Footer */}
          {footer && (
            <div className="mt-6 pt-6 border-t border-border">{footer}</div>
          )}
        </div>

        {/* Additional Links */}
        <div className="text-center mt-6">
          <p className="text-sm text-muted">
            By continuing, you agree to our{" "}
            <Link href="/terms" className="text-brand hover:text-brand-2">
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link href="/privacy" className="text-brand hover:text-brand-2">
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
          className="block text-sm font-medium text-fg mb-1"
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
            input disabled:bg-card-muted disabled:cursor-not-allowed
            ${
              error
                ? "border-red-300 bg-red-50 dark:border-red-500/50 dark:bg-red-500/10"
                : ""
            }
          `}
        />
        {error && (
          <p className="mt-1 text-sm text-red-600 dark:text-red-400">{error}</p>
        )}
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
    <Button
      type="submit"
      variant="primary"
      isLoading={isLoading}
      disabled={disabled}
      className="w-full"
    >
      {children}
    </Button>
  );
}
