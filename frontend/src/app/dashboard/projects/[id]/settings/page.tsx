import { Suspense } from 'react';
import { notFound, redirect } from 'next/navigation';
import { createClient } from '@/lib/supabase/server';
import SettingsPageClient from './SettingsPageClient';

interface PageProps {
  params: Promise<{
    id: string;
  }>;
}

async function getProject(projectId: string, token: string) {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/projects/${projectId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        cache: 'no-store',
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error('Failed to fetch project');
    }

    return response.json();
  } catch (error) {
    console.error('Error fetching project:', error);
    return null;
  }
}

export default async function ProjectSettingsPage({ params }: PageProps) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect('/auth/login');
  }

  // Get session for access token
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    redirect('/auth/login');
  }

  const { id } = await params;
  const project = await getProject(id, session.access_token);

  if (!project) {
    notFound();
  }

  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-surface flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand mx-auto"></div>
            <p className="mt-4 text-muted">Loading...</p>
          </div>
        </div>
      }
    >
      <SettingsPageClient
        projectId={id}
        initialProject={{
          name: project.name,
          description: project.description,
          prompt: project.prompt,
          subdomain: project.subdomain,
          seo_title: project.seo_title,
          seo_description: project.seo_description,
          favicon_url: project.favicon_url,
          whatsapp_number: project.whatsapp_number,
          published: project.published,
          deployment_url: project.deployment_url,
          last_deployed_at: project.last_deployed_at,
          last_edited_at: project.last_edited_at,
          created_at: project.created_at,
        }}
        user={{
          email: user.email!,
        }}
      />
    </Suspense>
  );
}
