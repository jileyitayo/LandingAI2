"use client";

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

interface SubscriptionDetailsCardProps {
  subscription?: Subscription;
  currentUsed: number;
  fallbackTierName?: string;
}

export default function SubscriptionDetailsCard({
  subscription,
  currentUsed,
  fallbackTierName = "free",
}: SubscriptionDetailsCardProps) {
  // Use subscription data if available, otherwise use fallback
  const displayName = subscription?.tier?.display_name || fallbackTierName.charAt(0).toUpperCase() + fallbackTierName.slice(1);
  const tierName = subscription?.tier?.tier_name || fallbackTierName;
  const description = subscription?.tier?.description || "Basic features for getting started";
  const dailyLimit = subscription?.tier?.daily_generation_limit || 5;
  const perMinuteLimit = subscription?.tier?.per_minute_limit || 1;
  const features = subscription?.tier?.features || ["5 generations per day", "1 request per minute"];
  const status = subscription?.status || "active";
  const isTrial = subscription?.trial_end && new Date(subscription.trial_end) > new Date();
  const cancelAtPeriodEnd = subscription?.cancel_at_period_end || false;

  // Calculate usage percentage
  const usagePercentage = Math.min((currentUsed / dailyLimit) * 100, 100);

  // Status badge color
  const getStatusColor = () => {
    switch (status) {
      case "active":
        return "bg-green-100 text-green-800 dark:bg-green-500/15 dark:text-green-400";
      case "trialing":
        return "bg-brand/10 text-brand";
      case "cancelled":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-500/15 dark:text-yellow-400";
      case "expired":
        return "bg-red-100 text-red-800 dark:bg-red-500/15 dark:text-red-400";
      case "past_due":
        return "bg-orange-100 text-orange-800";
      default:
        return "bg-card-muted text-fg";
    }
  };

  // Format date
  const formatDate = (dateString: string | null) => {
    if (!dateString) return null;
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-fg">Subscription Details</h2>
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor()}`}
        >
          {isTrial ? "Trial" : status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
      </div>

      {/* Plan Name and Description */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <h3 className="text-2xl font-bold text-fg">{displayName}</h3>
          {tierName === "free" && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-card-muted text-muted">
              Current Plan
            </span>
          )}
        </div>
        <p className="text-sm text-muted">{description}</p>
      </div>

      {/* Usage Progress */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-fg">Daily Usage</span>
          <span className="text-sm text-muted">
            {currentUsed} / {dailyLimit}
          </span>
        </div>
        <div className="w-full bg-card-muted rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full transition-all ${
              usagePercentage >= 100
                ? "bg-red-600 dark:bg-red-500"
                : usagePercentage >= 80
                ? "bg-yellow-500"
                : "bg-brand-gradient"
            }`}
            style={{ width: `${usagePercentage}%` }}
          ></div>
        </div>
        <p className="text-xs text-muted mt-1">
          {dailyLimit - currentUsed > 0
            ? `${dailyLimit - currentUsed} generations remaining today`
            : "Daily limit reached"}
        </p>
      </div>

      {/* Limits */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-card-muted rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <svg
              className="h-4 w-4 text-muted"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="text-xs font-medium text-muted">Daily Limit</span>
          </div>
          <p className="text-lg font-semibold text-fg">{dailyLimit}</p>
        </div>
        <div className="bg-card-muted rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <svg
              className="h-4 w-4 text-muted"
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
            <span className="text-xs font-medium text-muted">Per Minute</span>
          </div>
          <p className="text-lg font-semibold text-fg">{perMinuteLimit}</p>
        </div>
      </div>

      {/* Features */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-fg mb-3">Plan Features</h4>
        <ul className="space-y-2">
          {features.map((feature, index) => (
            <li key={index} className="flex items-start gap-2">
              <svg
                className="h-5 w-5 text-green-500 dark:text-green-400 flex-shrink-0 mt-0.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <span className="text-sm text-muted">{feature}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Billing Period */}
      {subscription?.current_period_start && subscription?.current_period_end && (
        <div className="mb-6 pb-6 border-b border-border">
          <h4 className="text-sm font-medium text-fg mb-2">Billing Period</h4>
          <p className="text-sm text-muted">
            {formatDate(subscription.current_period_start)} -{" "}
            {formatDate(subscription.current_period_end)}
          </p>
        </div>
      )}

      {/* Cancellation Notice */}
      {cancelAtPeriodEnd && subscription?.current_period_end && (
        <div className="mb-6 p-3 bg-yellow-50 border border-yellow-200 dark:bg-yellow-500/10 dark:border-yellow-500/30 rounded-md">
          <div className="flex items-start gap-2">
            <svg
              className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5"
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
            <div>
              <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300">Subscription Ending</p>
              <p className="text-xs text-yellow-700 dark:text-yellow-400/90 mt-1">
                Your subscription will end on {formatDate(subscription.current_period_end)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        {tierName === "free" && (
          <button className="flex-1 px-4 py-2 bg-brand-gradient text-brand-fg text-sm font-medium rounded-full shadow-glow-sm hover:shadow-glow focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 transition-all">
            Upgrade Plan
          </button>
        )}
        {tierName !== "free" && (
          <button className="flex-1 px-4 py-2 bg-card-muted text-fg text-sm font-medium rounded-full border border-border hover:bg-border focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/40 transition-colors">
            Manage Subscription
          </button>
        )}
      </div>
    </div>
  );
}
