"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/hooks/useAuth";
import { AuthForm, InputField, SubmitButton } from "@/components/AuthForm";

// Validation schema
const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

type LoginFormData = z.infer<typeof loginSchema>;

/**
 * Login page component
 * Allows existing users to sign in with email and password
 */
export default function LoginPage() {
  const router = useRouter();
  const { user, loading: authLoading, signIn } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (user && !authLoading) {
      router.push("/dashboard");
    }
  }, [user, authLoading, router]);

  const onSubmit = async (data: LoginFormData) => {
    const { error } = await signIn({
      email: data.email,
      password: data.password,
    });

    if (error) {
      // Set form-level error
      setError("root", {
        type: "manual",
        message: error,
      });
    } else {
      // Successful login - redirect handled by useAuth hook
      router.push("/dashboard");
    }
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

  // Don't show login form to authenticated users
  if (user) {
    return null;
  }

  return (
    <AuthForm
      title="Welcome back"
      subtitle="Sign in to your account to continue"
      onSubmit={handleSubmit(onSubmit)}
      error={errors.root?.message}
      footer={
        <div className="text-center space-y-3">
          <p className="text-sm text-gray-600">
            Don&apos;t have an account?{" "}
            <Link
              href="/auth/signup"
              className="text-indigo-600 hover:text-indigo-700 font-medium"
            >
              Sign up
            </Link>
          </p>
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

      <InputField
        label="Password"
        type="password"
        {...register("password")}
        placeholder="Enter your password"
        autoComplete="current-password"
        error={errors.password?.message}
        disabled={isSubmitting}
        required
      />

      <div className="flex items-center justify-end">
        <Link
          href="/auth/forgot-password"
          className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
        >
          Forgot password?
        </Link>
      </div>

      <SubmitButton isLoading={isSubmitting}>Sign in</SubmitButton>
    </AuthForm>
  );
}
