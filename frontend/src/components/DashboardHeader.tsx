"use client";

/**
 * DashboardHeader Component
 *
 * Reusable navigation header for dashboard pages
 * Includes user avatar, dropdown menu with navigation links, and sign out functionality
 */

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { useAuth } from "@/hooks/useAuth";
import { useUserProfile } from "@/hooks/useProjects";
import { shimmer, toBase64 } from "@/utils/value";
import FeedbackModal from "@/components/FeedbackModal";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

export default function DashboardHeader() {
  const router = useRouter();
  const { user, signOut } = useAuth();
  const { profile: userProfile } = useUserProfile();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [avatarError, setAvatarError] = useState(false);
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSignOut = async () => {
    await signOut();
    router.push("/auth/login");
  };

  const getInitials = () => {
    if (userProfile?.first_name && userProfile?.last_name) {
      return `${userProfile.first_name[0]}${userProfile.last_name[0]}`.toUpperCase();
    }
    if (userProfile?.first_name) {
      return userProfile.first_name[0].toUpperCase();
    }
    if (user?.email) {
      return user.email[0].toUpperCase();
    }
    return "U";
  };

  const getDisplayName = () => {
    if (userProfile?.first_name && userProfile?.last_name) {
      return `${userProfile.first_name} ${userProfile.last_name}`;
    }
    if (userProfile?.first_name) {
      return userProfile.first_name;
    }
    return user?.email;
  };

  return (
    <nav className="bg-card/80 backdrop-blur border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <button
              onClick={() => router.push("/dashboard")}
              className="font-display text-2xl font-bold bg-brand-gradient bg-clip-text text-transparent hover:opacity-80 transition-opacity cursor-pointer"
            >
              SiteSmith
            </button>
          </div>

          <div className="flex items-center gap-4">
            {/* Feedback Button */}
            <button
              onClick={() => setFeedbackModalOpen(true)}
              className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-fg bg-card border border-border rounded-full hover:bg-card-muted transition-colors shadow-sm"
              title="Share Feedback"
            >
              <svg
                className="w-5 h-5 text-muted"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"
                />
              </svg>
              <span className="hidden sm:inline">Feedback</span>
            </button>

            {/* User Avatar Dropdown */}
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center space-x-3 hover:bg-card-muted rounded-full px-3 py-2 transition-colors"
              >
                {/* Avatar */}
                <div className="flex items-center space-x-3">
                  {userProfile?.avatar_url && !avatarError ? (
                    <div className="relative w-10 h-10 rounded-full ring-2 ring-border overflow-hidden">
                      <Image
                        src={userProfile.avatar_url}
                        alt="Profile"
                        fill
                        sizes="40px"
                        className="object-cover"
                        priority={true}
                        quality={90}
                        placeholder="blur"
                        blurDataURL={`data:image/svg+xml;base64,${toBase64(shimmer(40, 40))}`}
                        onError={() => setAvatarError(true)}
                      />
                    </div>
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-brand-gradient-br flex items-center justify-center text-brand-fg font-semibold text-sm ring-2 ring-border">
                      {getInitials()}
                    </div>
                  )}

                  {/* User Info */}
                  <div className="text-left hidden sm:block">
                    <p className="text-sm font-medium text-fg">
                      {getDisplayName()}
                    </p>
                    <p className="text-xs text-muted">{user?.email}</p>
                  </div>
                </div>

                {/* Dropdown Arrow */}
                <svg
                  className={`w-4 h-4 text-muted transition-transform ${
                    dropdownOpen ? "rotate-180" : ""
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>

              {/* Dropdown Menu */}
              {dropdownOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-card rounded-xl shadow-lg border border-border py-1 z-50">
                  {/* User Info in Dropdown (mobile) */}
                  <div className="px-4 py-3 border-b border-border sm:hidden">
                    <p className="text-sm font-medium text-fg">
                      {getDisplayName()}
                    </p>
                    <p className="text-xs text-muted mt-0.5">{user?.email}</p>
                  </div>

                  {/* Dashboard Link */}
                  <button
                    onClick={() => {
                      router.push("/dashboard");
                      setDropdownOpen(false);
                    }}
                    className="w-full text-left px-4 py-2.5 text-sm text-fg hover:bg-card-muted flex items-center space-x-3 transition-colors"
                  >
                    <svg
                      className="w-5 h-5 text-muted"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                      />
                    </svg>
                    <span>Dashboard</span>
                  </button>

                  {/* Profile Link */}
                  <button
                    onClick={() => {
                      router.push("/dashboard/profile");
                      setDropdownOpen(false);
                    }}
                    className="w-full text-left px-4 py-2.5 text-sm text-fg hover:bg-card-muted flex items-center space-x-3 transition-colors"
                  >
                    <svg
                      className="w-5 h-5 text-muted"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                      />
                    </svg>
                    <span>Profile</span>
                  </button>

                  {/* Theme Toggle */}
                  <div className="px-4 py-2.5 border-t border-border flex items-center justify-between">
                    <span className="text-sm text-muted">Theme</span>
                    <ThemeToggle compact />
                  </div>

                  {/* Logout Button */}
                  <button
                    onClick={() => {
                      handleSignOut();
                      setDropdownOpen(false);
                    }}
                    className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10 flex items-center space-x-3 transition-colors border-t border-border"
                  >
                    <svg
                      className="w-5 h-5 text-red-500 dark:text-red-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                      />
                    </svg>
                    <span>Sign out</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Feedback Modal */}
      <FeedbackModal
        isOpen={feedbackModalOpen}
        onClose={() => setFeedbackModalOpen(false)}
      />
    </nav>
  );
}
