"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import ProfileForm from "@/components/ProfileForm";
import DashboardHeader from "@/components/DashboardHeader";
import SubscriptionDetailsCard from "@/components/SubscriptionDetailsCard";
import UsageChart from "@/components/UsageChart";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

interface SubscriptionTier {
  id: string;
  tier_name: string;
  display_name: string;
  description: string | null;
  daily_generation_limit: number;
  per_minute_limit: number;
  price_monthly: number;
  price_yearly: number;
  features: string[];
  is_active: boolean;
}

interface Subscription {
  id: string;
  status: string;
  tier: SubscriptionTier;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  cancelled_at: string | null;
  trial_start: string | null;
  trial_end: string | null;
}

interface UserProfile {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  avatar_url: string | null;
  subscription_tier: string;
  generation_count: number;
  current_period_generations: number;
  email_verified: boolean;
  created_at: string;
  updated_at: string;
  subscription?: Subscription;
}

interface AnalyticsData {
  period: string;
  granularity: string;
  data_points: Array<{
    timestamp: string;
    count: number;
    call_types: Record<string, number>;
  }>;
  total_calls: number;
  rpm_peak: number;
  rpd_average: number;
  breakdown_by_type: Record<string, number>;
}

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [analyticsPeriod, setAnalyticsPeriod] = useState<"24h" | "7d" | "30d" | "all">("7d");

  useEffect(() => {
    loadProfile();
    loadAnalytics("7d");
  }, []);

  const loadProfile = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const profileData = await api.users.getProfile();
      setProfile(profileData);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          // User is not authenticated, redirect to login
          router.push("/auth/login");
          return;
        }
        setError(err.message);
      } else {
        setError("Failed to load profile. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const loadAnalytics = async (period: "24h" | "7d" | "30d" | "all") => {
    setAnalyticsLoading(true);
    try {
      const granularity = period === "24h" ? "hourly" : "daily";
      const data = await api.users.getAnalytics(period, granularity);
      setAnalyticsData(data);
      setAnalyticsPeriod(period);
    } catch (err) {
      console.error("Failed to load analytics:", err);
      // Don't show error for analytics - just keep it empty
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const handleProfileUpdate = (updatedProfile: UserProfile) => {
    setProfile(updatedProfile);
  };

  const handlePeriodChange = (period: "24h" | "7d" | "30d" | "all") => {
    loadAnalytics(period);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand mx-auto mb-4"></div>
          <p className="text-muted">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-card rounded-2xl shadow-card border border-red-200 dark:border-red-500/30 p-6">
          <div className="text-center">
            <svg
              className="mx-auto h-12 w-12 text-red-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-fg">Error Loading Profile</h3>
            <p className="mt-2 text-sm text-muted">{error}</p>
            <button
              onClick={loadProfile}
              className="mt-4 px-4 py-2 text-sm font-medium text-brand-fg bg-brand-gradient rounded-full shadow-glow-sm hover:shadow-glow focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!profile) {
    return null;
  }

  return (
    <div className="min-h-screen bg-surface">
      <DashboardHeader />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-display text-3xl font-bold text-fg">Profile Settings</h1>
          <p className="mt-2 text-sm text-muted">
            Manage your account information, subscription, and view usage analytics.
          </p>
        </div>

        {/* Main Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Profile & Account Info */}
          <div className="lg:col-span-2 space-y-8">
            {/* Appearance */}
            <div className="card p-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold text-fg">Appearance</h2>
                  <p className="mt-1 text-sm text-muted">
                    Choose how SiteSmith looks to you. System matches your
                    device setting.
                  </p>
                </div>
                <ThemeToggle />
              </div>
            </div>

            {/* Profile Form */}
            <div>
              <h2 className="text-xl font-semibold text-fg mb-4">
                Personal Information
              </h2>
              <ProfileForm
                initialProfile={profile}
                onUpdate={handleProfileUpdate}
              />
            </div>

            {/* Usage Analytics */}
            <UsageChart
              data={analyticsData}
              isLoading={analyticsLoading}
              onPeriodChange={handlePeriodChange}
              currentPeriod={analyticsPeriod}
            />

            {/* Account Information */}
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-fg mb-4">
                Account Information
              </h2>
              <dl className="space-y-4">
                <div>
                  <dt className="text-sm font-medium text-muted">User ID</dt>
                  <dd className="mt-1 text-sm text-fg font-mono">{profile.id}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted">Email Verified</dt>
                  <dd className="mt-1">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        profile.email_verified
                          ? "bg-green-100 text-green-800 dark:bg-green-500/15 dark:text-green-400"
                          : "bg-yellow-100 text-yellow-800 dark:bg-yellow-500/15 dark:text-yellow-400"
                      }`}
                    >
                      {profile.email_verified ? "Verified" : "Not Verified"}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted">Account Created</dt>
                  <dd className="mt-1 text-sm text-fg">
                    {new Date(profile.created_at).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted">Last Updated</dt>
                  <dd className="mt-1 text-sm text-fg">
                    {new Date(profile.updated_at).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </dd>
                </div>
              </dl>
            </div>
          </div>

          {/* Right Column - Subscription & Quick Stats */}
          <div className="space-y-6">
            {/* Subscription Details */}
            <SubscriptionDetailsCard
              subscription={profile.subscription}
              currentUsed={profile.current_period_generations}
              fallbackTierName={profile.subscription_tier}
            />

            {/* Quick Stats */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-fg mb-4">Quick Stats</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <svg
                      className="h-5 w-5 text-green-600 dark:text-green-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <span className="text-sm font-medium text-fg">Total Projects</span>
                  </div>
                  <span className="text-lg font-bold text-fg">{profile.generation_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <svg
                      className="h-5 w-5 text-brand"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 10V3L4 14h7v7l9-11h-7z"
                      />
                    </svg>
                    <span className="text-sm font-medium text-fg">Daily Used</span>
                  </div>
                  <span className="text-lg font-bold text-fg">{profile.current_period_generations}</span>
                </div>
                {analyticsData && (
                  <>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <svg
                          className="h-5 w-5 text-brand-2"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                          />
                        </svg>
                        <span className="text-sm font-medium text-fg">Total Calls</span>
                      </div>
                      <span className="text-lg font-bold text-fg">{analyticsData.total_calls}</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

