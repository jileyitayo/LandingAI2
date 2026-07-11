'use client';

import { GenerationProvider } from '@/contexts/GenerationContext';

/**
 * Dashboard layout: wraps every dashboard route in the generation tracker so
 * in-flight website generations survive navigation (live banner + card
 * progress + resume on /dashboard/new).
 */
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <GenerationProvider>{children}</GenerationProvider>;
}
