"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/hooks/useAuth";
import { AuthForm, InputField, SubmitButton } from "@/components/AuthForm";
import { GoogleSignInButton } from "@/components/GoogleSignInButton";

// Validation schema
const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

type LoginFormData = z.infer<typeof loginSchema>;

/**
 * Login form component that uses search params
 */
function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading: authLoading, signIn, signInWithGoogle } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  // Check for error in URL params (from OAuth callback)
  useEffect(() => {
    const error = searchParams.get("error");
    if (error) {
      setError("root", {
        type: "manual",
        message: decodeURIComponent(error),
      });
    }
  }, [searchParams, setError]);

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
      <div className="min-h-screen flex items-center justify-center bg-surface">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand mx-auto"></div>
          <p className="mt-4 text-muted">Loading...</p>
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
          <p className="text-sm text-muted">
            Don&apos;t have an account?{" "}
            <Link
              href="/auth/signup"
              className="text-brand hover:text-brand-2 font-medium"
            >
              Sign up
            </Link>
          </p>
        </div>
      }
    >
      <GoogleSignInButton
        onSignIn={handleGoogleSignIn}
        mode="signin"
        disabled={isSubmitting}
      />

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-border"></div>
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-card text-muted">Or continue with email</span>
        </div>
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
        placeholder="Enter your password"
        autoComplete="current-password"
        error={errors.password?.message}
        disabled={isSubmitting}
        required
      />

      <div className="flex items-center justify-end">
        <Link
          href="/auth/forgot-password"
          className="text-sm text-brand hover:text-brand-2 font-medium"
        >
          Forgot password?
        </Link>
      </div>

      <SubmitButton isLoading={isSubmitting}>Sign in</SubmitButton>
    </AuthForm>
  );
}

/**
 * Login page component
 * Allows existing users to sign in with email and password
 */
export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-surface">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand mx-auto"></div>
            <p className="mt-4 text-muted">Loading...</p>
          </div>
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
