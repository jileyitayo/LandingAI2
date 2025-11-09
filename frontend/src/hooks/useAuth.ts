"use client";

import { useEffect, useState } from "react";
import { User } from "@supabase/supabase-js";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import { getNormalizedOrigin } from "@/utils/url";

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

interface SignUpData {
  email: string;
  password: string;
  fullName?: string;
}

interface LoginData {
  email: string;
  password: string;
}

/**
 * Custom hook for managing authentication state
 * Handles user session, sign up, login, logout, and password reset
 */
export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null,
  });
  const router = useRouter();
  const supabase = createClient();

  useEffect(() => {
    // Get initial session
    const getSession = async () => {
      try {
        const {
          data: { session },
          error,
        } = await supabase.auth.getSession();

        if (error) throw error;

        setAuthState({
          user: session?.user ?? null,
          loading: false,
          error: null,
        });
      } catch (error) {
        setAuthState({
          user: null,
          loading: false,
          error:
            error instanceof Error ? error.message : "Failed to get session",
        });
      }
    };

    getSession();

    // Listen for auth state changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      setAuthState({
        user: session?.user ?? null,
        loading: false,
        error: null,
      });

      // Redirect on sign in/sign up
      // Redirect on sign in/sign up (but only if not already on a dashboard page)
      if (event === "SIGNED_IN") {
        const currentPath = window.location.pathname;
        // Only redirect if coming from auth pages or root
        if (currentPath === '/' || currentPath.startsWith('/auth/')) {
          router.push("/dashboard");
        }
      }

      // Redirect on sign out
      if (event === "SIGNED_OUT") {
        router.push("/auth/login");
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [supabase, router]);

  /**
   * Sign up a new user with email and password
   */
  const signUp = async ({ email, password, fullName }: SignUpData) => {
    try {
      setAuthState((prev) => ({ ...prev, loading: true, error: null }));

      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: fullName ? { full_name: fullName } : {},
          // Use normalized origin to ensure consistent redirect URLs
          emailRedirectTo: `${getNormalizedOrigin()}/auth/callback`,
        },
      });

      if (error) throw error;

      setAuthState({
        user: data.user,
        loading: false,
        error: null,
      });

      return { data, error: null };
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to sign up";
      setAuthState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      return { data: null, error: errorMessage };
    }
  };

  /**
   * Sign in an existing user with email and password
   */
  const signIn = async ({ email, password }: LoginData) => {
    try {
      setAuthState((prev) => ({ ...prev, loading: true, error: null }));

      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) throw error;

      setAuthState({
        user: data.user,
        loading: false,
        error: null,
      });

      return { data, error: null };
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to sign in";
      setAuthState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      return { data: null, error: errorMessage };
    }
  };

  /**
   * Sign out the current user
   */
  const signOut = async () => {
    try {
      setAuthState((prev) => ({ ...prev, loading: true, error: null }));

      const { error } = await supabase.auth.signOut();

      if (error) throw error;

      setAuthState({
        user: null,
        loading: false,
        error: null,
      });

      return { error: null };
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to sign out";
      setAuthState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      return { error: errorMessage };
    }
  };

  /**
   * Send password reset email
   */
  const resetPassword = async (email: string) => {
    try {
      setAuthState((prev) => ({ ...prev, loading: true, error: null }));

      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        // Use normalized origin to ensure consistent redirect URLs
        redirectTo: `${getNormalizedOrigin()}/auth/reset-password`,
      });

      if (error) throw error;

      setAuthState((prev) => ({ ...prev, loading: false, error: null }));

      return { error: null };
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to send reset email";
      setAuthState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      return { error: errorMessage };
    }
  };

  /**
   * Update user password
   */
  const updatePassword = async (newPassword: string) => {
    try {
      setAuthState((prev) => ({ ...prev, loading: true, error: null }));

      const { error } = await supabase.auth.updateUser({
        password: newPassword,
      });

      if (error) throw error;

      setAuthState((prev) => ({ ...prev, loading: false, error: null }));

      return { error: null };
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to update password";
      setAuthState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      return { error: errorMessage };
    }
  };

  /**
   * Sign in with Google OAuth
   */
  const signInWithGoogle = async () => {
    try {
      setAuthState((prev) => ({ ...prev, loading: true, error: null }));

      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          // Use normalized origin to ensure consistent redirect URLs
          // This fixes the issue where 0.0.0.0:3000 causes CORS and redirect problems
          redirectTo: `${getNormalizedOrigin()}/auth/callback`,
          queryParams: {
            access_type: "offline",
            prompt: "consent",
          },
        },
      });

      if (error) throw error;

      // The redirect happens automatically, so we don't need to set state here
      return { data, error: null };
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to sign in with Google";
      setAuthState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      return { data: null, error: errorMessage };
    }
  };

  return {
    user: authState.user,
    loading: authState.loading,
    error: authState.error,
    signUp,
    signIn,
    signOut,
    resetPassword,
    updatePassword,
    signInWithGoogle,
  };
}
