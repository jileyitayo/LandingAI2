"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

interface UserProfile {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Example component demonstrating how to fetch user data from the backend API
 * This shows the integration between frontend Supabase session and backend authentication
 */
export function UserProfileCard() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const supabase = createClient();

  useEffect(() => {
    async function fetchUserFromBackend() {
      try {
        setLoading(true);
        setError(null);

        // Call backend API - it will automatically include the Authorization header
        // with the access token from the current Supabase session
        const userData = await api.auth.getUser();
        setUser(userData);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);

          // Handle authentication errors
          if (err.status === 401) {
            // Token expired or invalid - redirect to login
            console.error("Authentication failed, redirecting to login");
            router.push("/auth/login");
          } else if (err.status === 403) {
            // Forbidden
            setError("You don't have permission to access this resource");
          }
        } else {
          setError("An unexpected error occurred");
        }
      } finally {
        setLoading(false);
      }
    }

    fetchUserFromBackend();
  }, [router]);

  const handleLogout = async () => {
    try {
      // Option 1: Call backend logout endpoint (invalidates session on backend)
      await api.auth.logout();

      // Also sign out from Supabase client
      await supabase.auth.signOut();

      // Redirect to login
      router.push("/auth/login");
    } catch (err) {
      console.error("Logout error:", err);
      // Even if backend logout fails, sign out locally
      await supabase.auth.signOut();
      router.push("/auth/login");
    }
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-medium mb-2">Error Loading Profile</h3>
        <p className="text-red-600 text-sm">{error}</p>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">
            {user.first_name && user.last_name
              ? `${user.first_name} ${user.last_name}`
              : user.email}
          </h2>
          <p className="text-sm text-gray-500">{user.email}</p>
        </div>
        <button
          onClick={handleLogout}
          className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Logout
        </button>
      </div>

      <div className="border-t border-gray-200 pt-4">
        <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm font-medium text-gray-500">User ID</dt>
            <dd className="mt-1 text-sm text-gray-900 font-mono">{user.id}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Member Since</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {new Date(user.created_at).toLocaleDateString()}
            </dd>
          </div>
          {user.first_name && (
            <div>
              <dt className="text-sm font-medium text-gray-500">First Name</dt>
              <dd className="mt-1 text-sm text-gray-900">{user.first_name}</dd>
            </div>
          )}
          {user.last_name && (
            <div>
              <dt className="text-sm font-medium text-gray-500">Last Name</dt>
              <dd className="mt-1 text-sm text-gray-900">{user.last_name}</dd>
            </div>
          )}
        </dl>
      </div>

      <div className="mt-4 p-3 bg-blue-50 rounded-md">
        <p className="text-xs text-blue-800">
          <strong>Note:</strong> This data was fetched from the FastAPI backend,
          which verified your Supabase access token before returning your user
          information. The Authorization header was automatically included by the
          API client.
        </p>
      </div>
    </div>
  );
}
