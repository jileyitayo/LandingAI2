"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/hooks/useAuth";
import { AuthForm, InputField, SubmitButton } from "@/components/AuthForm";

// Validation schema
const resetPasswordSchema = z
  .object({
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[a-z]/, "Password must contain at least one lowercase letter")
      .regex(/[0-9]/, "Password must contain at least one number"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

/**
 * Reset password page component - Inner component
 * Allows users to set a new password after clicking the reset link
 */
function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { updatePassword } = useAuth();
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [isValidToken, setIsValidToken] = useState(true);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
  });

  // Check if we have a valid token from the URL
  useEffect(() => {
    const type = searchParams.get("type");
    const accessToken = searchParams.get("access_token");

    // Validate that this is a recovery flow
    if (type !== "recovery" || !accessToken) {
      setIsValidToken(false);
    }
  }, [searchParams]);

  const onSubmit = async (data: ResetPasswordFormData) => {
    const { error } = await updatePassword(data.password);

    if (error) {
      setError("root", {
        type: "manual",
        message: error,
      });
    } else {
      setShowSuccessMessage(true);

      // Redirect to login after 3 seconds
      setTimeout(() => {
        router.push("/auth/login");
      }, 3000);
    }
  };

  // Show error if token is invalid
  if (!isValidToken) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50 px-4">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100 text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>

            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Invalid or expired link
            </h2>

            <p className="text-gray-600 mb-6">
              This password reset link is invalid or has expired. Please request
              a new password reset link.
            </p>

            <div className="space-y-3">
              <Link
                href="/auth/forgot-password"
                className="block w-full px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-colors"
              >
                Request new link
              </Link>

              <Link
                href="/auth/login"
                className="block w-full px-6 py-2.5 bg-white text-gray-700 rounded-lg font-medium border border-gray-300 hover:bg-gray-50 transition-colors"
              >
                Back to login
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show success message after password is reset
  if (showSuccessMessage) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50 px-4">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-green-600"
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

            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Password updated!
            </h2>

            <p className="text-gray-600 mb-6">
              Your password has been successfully updated. You can now sign in
              with your new password.
            </p>

            <p className="text-sm text-gray-500 mb-6">
              Redirecting to login page...
            </p>

            <Link
              href="/auth/login"
              className="inline-block px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-colors"
            >
              Go to login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <AuthForm
      title="Set new password"
      subtitle="Enter your new password below"
      onSubmit={handleSubmit(onSubmit)}
      error={errors.root?.message}
      footer={
        <div className="text-center">
          <Link
            href="/auth/login"
            className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
          >
            ← Back to login
          </Link>
        </div>
      }
    >
      <InputField
        label="New password"
        type="password"
        {...register("password")}
        placeholder="Create a strong password"
        autoComplete="new-password"
        error={errors.password?.message}
        disabled={isSubmitting}
        required
      />

      <InputField
        label="Confirm new password"
        type="password"
        {...register("confirmPassword")}
        placeholder="Confirm your new password"
        autoComplete="new-password"
        error={errors.confirmPassword?.message}
        disabled={isSubmitting}
        required
      />

      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-800">
          <strong>Password requirements:</strong>
        </p>
        <ul className="text-xs text-blue-700 mt-1 space-y-1 list-disc list-inside">
          <li>At least 8 characters long</li>
          <li>Contains uppercase and lowercase letters</li>
          <li>Contains at least one number</li>
        </ul>
      </div>

      <SubmitButton isLoading={isSubmitting}>Update password</SubmitButton>
    </AuthForm>
  );
}

/**
 * Reset password page with Suspense wrapper
 */
export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
      }
    >
      <ResetPasswordContent />
    </Suspense>
  );
}
