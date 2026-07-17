'use client';

import Link from 'next/link';
import ProjectSettingsForm from '@/components/ProjectSettingsForm';
import DashboardHeader from '@/components/DashboardHeader';

interface SettingsPageClientProps {
  projectId: string;
  initialProject: {
    name: string;
    description?: string;
    prompt?: string;
    subdomain?: string;
    seo_title?: string;
    seo_description?: string;
    favicon_url?: string;
    whatsapp_number?: string;
    published?: boolean;
    deployment_url?: string;
    last_deployed_at?: string;
    last_edited_at?: string;
    created_at?: string;
  };
  user: {
    email: string;
  };
}

export default function SettingsPageClient({
  projectId,
  initialProject,
}: SettingsPageClientProps) {

  return (
    <div className="min-h-screen bg-surface">
      <DashboardHeader />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb and Header */}
        <div className="mb-8">
          <nav className="flex items-center space-x-2 text-sm text-muted mb-4">
            <Link href="/dashboard" className="hover:text-fg transition-colors">
              Dashboard
            </Link>
            <span>/</span>
            <Link
              href={`/dashboard/projects/${projectId}`}
              className="hover:text-fg transition-colors"
            >
              {initialProject.name}
            </Link>
            <span>/</span>
            <span className="text-fg">Settings</span>
          </nav>

          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-fg">Project Settings</h1>
              <p className="mt-1 text-sm text-muted">
                Configure your project settings, subdomain, SEO, and integrations
              </p>
            </div>
            <Link
              href={`/dashboard/projects/${projectId}`}
              className="inline-flex items-center gap-2 px-4 py-2 border border-border rounded-lg bg-card hover:bg-card-muted transition-colors shadow-sm"
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

