'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import ProjectSettingsForm from '@/components/ProjectSettingsForm';
import { api } from '@/lib/api';

interface SettingsPageClientProps {
  projectId: string;
  initialProject: {
    name: string;
    description?: string;
    subdomain?: string;
    seo_title?: string;
    seo_description?: string;
    whatsapp_number?: string;
    published?: boolean;
  };
  user: {
    email: string;
  };
}

export default function SettingsPageClient({
  projectId,
  initialProject,
  user,
}: SettingsPageClientProps) {
  const router = useRouter();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [userProfile, setUserProfile] = useState<{
    avatar_url?: string | null;
    first_name?: string | null;
    last_name?: string | null;
  } | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch user profile for avatar
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const profile = await api.users.getProfile();
        setUserProfile(profile);
      } catch (error) {
        console.error('Failed to fetch user profile:', error);
      }
    };

    fetchProfile();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSignOut = async () => {
    try {
      const { createClient } = await import('@/lib/supabase/client');
      const supabase = createClient();
      await supabase.auth.signOut();
      router.push('/auth/login');
    } catch (error) {
      console.error('Failed to sign out:', error);
    }
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
    return 'U';
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
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Header */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Link href="/dashboard">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent cursor-pointer">
                  SiteSmith
                </h1>
              </Link>
            </div>

            <div className="flex items-center gap-4">
              {/* Browse Templates Button */}
              <button
                onClick={() => router.push('/dashboard/templates')}
                className="px-4 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-700 transition-colors"
              >
                Browse Templates
              </button>

              {/* User Avatar Dropdown */}
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  className="flex items-center space-x-3 hover:bg-gray-50 rounded-lg px-3 py-2 transition-colors"
                >
                  {/* Avatar */}
                  <div className="flex items-center space-x-3">
                    {userProfile?.avatar_url ? (
                      <img
                        src={userProfile.avatar_url}
                        alt="Profile"
                        className="w-10 h-10 rounded-full object-cover ring-2 ring-gray-200"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-semibold text-sm ring-2 ring-gray-200">
                        {getInitials()}
                      </div>
                    )}

                    {/* User Info */}
                    <div className="text-left hidden sm:block">
                      <p className="text-sm font-medium text-gray-900">
                        {getDisplayName()}
                      </p>
                      <p className="text-xs text-gray-500">{user.email}</p>
                    </div>
                  </div>

                  {/* Dropdown Arrow */}
                  <svg
                    className={`w-4 h-4 text-gray-500 transition-transform ${
                      dropdownOpen ? 'rotate-180' : ''
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
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                    {/* User Info in Dropdown (mobile) */}
                    <div className="px-4 py-3 border-b border-gray-100 sm:hidden">
                      <p className="text-sm font-medium text-gray-900">
                        {getDisplayName()}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">{user.email}</p>
                    </div>

                    {/* Profile Link */}
                    <button
                      onClick={() => {
                        router.push('/dashboard/profile');
                        setDropdownOpen(false);
                      }}
                      className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 flex items-center space-x-3 transition-colors"
                    >
                      <svg
                        className="w-5 h-5 text-gray-400"
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

                    {/* Logout Button */}
                    <button
                      onClick={() => {
                        handleSignOut();
                        setDropdownOpen(false);
                      }}
                      className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 flex items-center space-x-3 transition-colors"
                    >
                      <svg
                        className="w-5 h-5 text-red-500"
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
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb and Header */}
        <div className="mb-8">
          <nav className="flex items-center space-x-2 text-sm text-gray-500 mb-4">
            <Link href="/dashboard" className="hover:text-gray-700 transition-colors">
              Dashboard
            </Link>
            <span>/</span>
            <Link
              href={`/dashboard/projects/${projectId}`}
              className="hover:text-gray-700 transition-colors"
            >
              {initialProject.name}
            </Link>
            <span>/</span>
            <span className="text-gray-900">Settings</span>
          </nav>

          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Project Settings</h1>
              <p className="mt-1 text-sm text-gray-500">
                Configure your project settings, subdomain, SEO, and integrations
              </p>
            </div>
            <Link
              href={`/dashboard/projects/${projectId}`}
              className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 transition-colors shadow-sm"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                />
              </svg>
              Back to Editor
            </Link>
          </div>
        </div>

        {/* Settings Form */}
        <ProjectSettingsForm projectId={projectId} initialData={initialProject} />
      </main>
    </div>
  );
}

