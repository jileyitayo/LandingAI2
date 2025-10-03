"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { UserProfileCard } from "@/components/UserProfileCard";

/**
 * Dashboard page - Protected route
 * Requires authentication to access
 */
export default function DashboardPage() {
  const router = useRouter();
  const { user, loading, signOut } = useAuth();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/login");
    }
  }, [user, loading, router]);

  const handleSignOut = async () => {
    await signOut();
    router.push("/auth/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                SiteSmith
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">{user.email}</span>
              <button
                onClick={handleSignOut}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="space-y-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Welcome to your Dashboard! 🎉
            </h2>
            <p className="text-gray-600 mb-8">
              You&apos;re successfully authenticated. This dashboard demonstrates
              both frontend Supabase auth and backend API integration.
            </p>
          </div>

          {/* Frontend Supabase User Info */}
          <div className="max-w-2xl mx-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Frontend Supabase Session
            </h3>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <span className="font-medium text-gray-700">Email:</span>
                  <span className="text-gray-900">{user.email}</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <span className="font-medium text-gray-700">User ID:</span>
                  <span className="text-gray-900 font-mono text-sm">
                    {user.id}
                  </span>
                </div>

                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200">
                  <span className="font-medium text-green-700">
                    Email Verified:
                  </span>
                  <span className="text-green-900">
                    {user.email_confirmed_at ? "✓ Yes" : "✗ No"}
                  </span>
                </div>
              </div>
              
              <div className="mt-4 p-3 bg-blue-50 rounded-md">
                <p className="text-xs text-blue-800">
                  <strong>Source:</strong> This data comes from the Supabase client
                  session stored in your browser (frontend only).
                </p>
              </div>
            </div>
          </div>

          {/* Backend API User Info */}
          <div className="max-w-2xl mx-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Backend API Verified User
            </h3>
            <UserProfileCard />
          </div>

          <div className="text-center mt-8">
            <p className="text-sm text-gray-500">
              Phase 2: Authentication - Frontend + Backend Integration Complete ✓
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
