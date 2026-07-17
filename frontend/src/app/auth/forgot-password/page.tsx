"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/hooks/useAuth";
import { AuthForm, InputField, SubmitButton } from "@/components/AuthForm";

// Validation schema
const forgotPasswordSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
});

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

/**
 * Forgot password page component
 * Allows users to request a password reset link via email
 */
export default function ForgotPasswordPage() {
  const { resetPassword } = useAuth();
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    const { error } = await resetPassword(data.email);

    if (error) {
      setError("root", {
        type: "manual",
        message: error,
      });
    } else {
      setSubmittedEmail(data.email);
      setShowSuccessMessage(true);
    }
  };

  // Show success message after email is sent
  if (showSuccessMessage) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface px-4">
        <div className="w-full max-w-md">
          <div className="card p-8 text-center">
            <div className="w-16 h-16 bg-brand/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-brand"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 19v-8.93a2 2 0 01.89-1.664l7-4.666a2 2 0 012.22 0l7 4.666A2 2 0 0121 10.07V19M3 19a2 2 0 002 2h14a2 2 0 002-2M3 19l6.75-4.5M21 19l-6.75-4.5M3 10l6.75 4.5M21 10l-6.75 4.5m0 0l-1.14.76a2 2 0 01-2.22 0l-1.14-.76"
                />
              </svg>
            </div>

            <h2 className="font-display text-2xl font-semibold text-fg mb-2">
              Check your email
            </h2>

            <p className="text-muted mb-2">
              We&apos;ve sent a password reset link to:
            </p>

            <p className="font-medium text-fg mb-6">{submittedEmail}</p>

            <div className="bg-brand/5 border border-brand/20 rounded-lg p-4 mb-6">
              <p className="text-sm text-brand">
                <strong>Note:</strong> The link will expire in 1 hour. If you
                don&apos;t see the email, check your spam folder.
              </p>
            </div>

            <div className="space-y-3">
              <Link
                href="/auth/login"
                className="block w-full px-6 py-2.5 bg-brand-gradient text-brand-fg rounded-full font-medium shadow-glow-sm hover:shadow-glow transition-all"
              >
                Back to login
              </Link>

              <button
                onClick={() => setShowSuccessMessage(false)}
                className="block w-full px-6 py-2.5 bg-card text-fg rounded-full font-medium border border-border hover:bg-card-muted transition-colors"
              >
                Resend email
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <AuthForm
      title="Reset your password"
      subtitle="Enter your email address and we'll send you a reset link"
      onSubmit={handleSubmit(onSubmit)}
      error={errors.root?.message}
      footer={
        <div className="text-center">
          <Link
            href="/auth/login"
            className="text-sm text-brand hover:text-brand-2 font-medium"
          >
            ← Back to login
          </Link>
        </div>
      }
    >
      <InputField
        label="Email address"
        type="email"
        {...register("email")}
        placeholder="you@example.com"
        autoComplete="email"
        error={errors.email?.message}
        disabled={isSubmitting}
        required
      />

      <SubmitButton isLoading={isSubmitting}>Send reset link</SubmitButton>

      <div className="mt-4 p-4 bg-card-muted rounded-lg border border-border">
        <p className="text-sm text-muted">
          <strong>Need help?</strong> If you&apos;re having trouble resetting
          your password, please contact support.
        </p>
      </div>
    </AuthForm>
  );
}
