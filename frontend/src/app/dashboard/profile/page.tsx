"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import ProfileForm from "@/components/ProfileForm";
import DashboardHeader from "@/components/DashboardHeader";
import SubscriptionDetailsCard from "@/components/SubscriptionDetailsCard";
import UsageChart from "@/components/UsageChart";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { AlertTriangle } from "lucide-react";

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
            <AlertTriangle className="mx-auto h-12 w-12 text-red-400" aria-hidden="true" />
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
          {/* Left Column - Profile & Usage */}
          <div className="lg:col-span-2 space-y-6">
            <ProfileForm
              initialProfile={profile}
              onUpdate={handleProfileUpdate}
            />

            <UsageChart
              data={analyticsData}
              isLoading={analyticsLoading}
              onPeriodChange={handlePeriodChange}
              currentPeriod={analyticsPeriod}
            />
          </div>

          {/* Right Column - Plan & Preferences */}
          <div className="space-y-6">
            <SubscriptionDetailsCard
              subscription={profile.subscription}
              currentUsed={profile.current_period_generations}
              fallbackTierName={profile.subscription_tier}
              totalGenerations={profile.generation_count}
            />

            <div className="card p-6">
              <h2 className="text-xl font-semibold text-fg">Appearance</h2>
              <p className="mt-1 mb-4 text-sm text-muted">
                Choose how SiteSmith looks to you.
              </p>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

