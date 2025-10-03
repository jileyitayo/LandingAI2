"use client";

import { useEffect, useState } from "react";
import { User } from "@supabase/supabase-js";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";

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
      if (event === "SIGNED_IN") {
        router.push("/dashboard");
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
          emailRedirectTo: `${window.location.origin}/auth/callback`,
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
        redirectTo: `${window.location.origin}/auth/reset-password`,
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

  return {
    user: authState.user,
    loading: authState.loading,
    error: authState.error,
    signUp,
    signIn,
    signOut,
    resetPassword,
    updatePassword,
  };
}
