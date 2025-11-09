"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/hooks/useAuth";
import { AuthForm, InputField, SubmitButton } from "@/components/AuthForm";
import { api } from "@/lib/api";
import { GoogleSignInButton } from "@/components/GoogleSignInButton";

// Validation schema
const signupSchema = z
  .object({
    firstName: z
      .string()
      .min(2, "First name must be at least 2 characters")
      .optional(),
    lastName: z
      .string()
      .min(2, "Last name must be at least 2 characters")
      .optional(),
    email: z.string().email("Please enter a valid email address"),
    password: z
      .string()
      .min(6, "Password must be at least 8 characters"),
      // UNCOMMENT THIS FOR PRODUCTION
      // .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      // .regex(/[a-z]/, "Password must contain at least one lowercase letter")
      // .regex(/[0-9]/, "Password must contain at least one number"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

type SignupFormData = z.infer<typeof signupSchema>;

/**
 * Signup page component
 * Allows new users to create an account with email verification
 */
export default function SignupPage() {
  const router = useRouter();
  const { user, loading: authLoading, signUp, signInWithGoogle } = useAuth();
  const [showVerificationMessage, setShowVerificationMessage] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
  });

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (user && !authLoading) {
      router.push("/dashboard");
    }
  }, [user, authLoading, router]);

  const onSubmit = async (data: SignupFormData) => {
    // Combine first and last name, only if at least one is provided
    const fullName = (() => {
      const firstName = data.firstName?.trim() || "";
      const lastName = data.lastName?.trim() || "";

      if (firstName && lastName) {
        return `${firstName} ${lastName}`;
      } else if (firstName) {
        return firstName;
      } else if (lastName) {
        return lastName;
      }
      return undefined; // No names provided
    })();

    const { error } = await signUp({
      email: data.email,
      password: data.password,
      fullName,
    });

    if (error) {
      setError("root", {
        type: "manual",
        message: error,
      });
    } else {
      // After successful signup, update the user profile with first/last names
      try {
        // Only update if we have names to save
        if (data.firstName || data.lastName) {
          await api.users.updateProfile({
            first_name: data.firstName?.trim() || undefined,
            last_name: data.lastName?.trim() || undefined,
          });
        }
      } catch (profileError) {
        // Log the error but don't block the signup flow
        console.error("Failed to update profile:", profileError);
      }
      
      // Show verification message
      setShowVerificationMessage(true);
    }
  };

  const handleGoogleSignIn = async () => {
    const { error } = await signInWithGoogle();
    if (error) {
      setError("root", {
        type: "manual",
        message: error,
      });
    }
    return { error };
  };

  // Show loading state while checking auth
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't show signup form to authenticated users
  if (user) {
    return null;
  }

  // Show email verification message after successful signup
  if (showVerificationMessage) {
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
                  d="M3 19v-8.93a2 2 0 01.89-1.664l7-4.666a2 2 0 012.22 0l7 4.666A2 2 0 0121 10.07V19M3 19a2 2 0 002 2h14a2 2 0 002-2M3 19l6.75-4.5M21 19l-6.75-4.5M3 10l6.75 4.5M21 10l-6.75 4.5m0 0l-1.14.76a2 2 0 01-2.22 0l-1.14-.76"
                />
              </svg>
            </div>

            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Check your email
            </h2>

            <p className="text-gray-600 mb-6">
              We&apos;ve sent a verification link to your email address. Please
              click the link to verify your account and complete the signup
              process.
            </p>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <p className="text-sm text-blue-800">
                <strong>Tip:</strong> If you don&apos;t see the email, check
                your spam folder.
              </p>
            </div>

            <Link
              href="/auth/login"
              className="inline-block px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-colors"
            >
              Back to login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <AuthForm
      title="Create your account"
      subtitle="Start building beautiful websites with AI"
      onSubmit={handleSubmit(onSubmit)}
      error={errors.root?.message}
      footer={
        <div className="text-center">
          <p className="text-sm text-gray-600">
            Already have an account?{" "}
            <Link
              href="/auth/login"
              className="text-indigo-600 hover:text-indigo-700 font-medium"
            >
              Sign in
            </Link>
          </p>
        </div>
      }
    >
      <GoogleSignInButton
        onSignIn={handleGoogleSignIn}
        mode="signup"
        disabled={isSubmitting}
      />

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300"></div>
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-white text-gray-500">Or continue with email</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <InputField
          label="First name"
          type="text"
          {...register("firstName")}
          placeholder="John"
          autoComplete="given-name"
          error={errors.firstName?.message}
          disabled={isSubmitting}
        />

        <InputField
          label="Last name"
          type="text"
          {...register("lastName")}
          placeholder="Doe"
          autoComplete="family-name"
          error={errors.lastName?.message}
          disabled={isSubmitting}
        />
      </div>

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

      <InputField
        label="Password"
        type="password"
        {...register("password")}
        placeholder="Create a strong password"
        autoComplete="new-password"
        error={errors.password?.message}
        disabled={isSubmitting}
        required
      />

      <InputField
        label="Confirm password"
        type="password"
        {...register("confirmPassword")}
        placeholder="Confirm your password"
        autoComplete="new-password"
        error={errors.confirmPassword?.message}
        disabled={isSubmitting}
        required
      />

      <SubmitButton isLoading={isSubmitting}>Create account</SubmitButton>
    </AuthForm>
  );
}
