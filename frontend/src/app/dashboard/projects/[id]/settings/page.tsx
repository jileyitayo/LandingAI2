import { Suspense } from 'react';
import { notFound, redirect } from 'next/navigation';
import { createClient } from '@/lib/supabase/server';
import SettingsPageClient from './SettingsPageClient';

interface PageProps {
  params: {
    id: string;
  };
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
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    redirect('/auth/login');
  }

  const project = await getProject(params.id, session.access_token);

  if (!project) {
    notFound();
  }

  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
      }
    >
      <SettingsPageClient
        projectId={params.id}
        initialProject={{
          name: project.name,
          description: project.description,
          subdomain: project.subdomain,
          seo_title: project.seo_title,
          seo_description: project.seo_description,
          whatsapp_number: project.whatsapp_number,
          published: project.published,
        }}
        user={{
          email: session.user.email!,
        }}
      />
    </Suspense>
  );
}
