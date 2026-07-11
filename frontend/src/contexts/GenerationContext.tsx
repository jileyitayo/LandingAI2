'use client';

/**
 * GenerationContext
 *
 * Dashboard-wide tracker for in-flight website generations. Generation runs
 * server-side regardless of navigation — this context makes the frontend
 * re-attach to it: on mount it finds projects stuck in 'generating', polls
 * each one's status, and exposes live progress to any dashboard page
 * (banner, project cards, the /dashboard/new resume view).
 */

import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/api';

export interface ActiveGeneration {
  projectId: string;
  name: string;
  status: 'generating' | 'completed' | 'failed';
  progress: number;
  stage?: string;
  stageMessage?: string;
}

interface GenerationContextValue {
  active: ActiveGeneration[];
  /** Start tracking a generation (call right after kicking one off) */
  track: (projectId: string, name?: string) => void;
}

const GenerationContext = createContext<GenerationContextValue | null>(null);

/** Null outside the provider so shared components can degrade gracefully */
export function useActiveGenerations(): GenerationContextValue | null {
  return useContext(GenerationContext);
}

const POLL_INTERVAL_MS = 6000;

export function GenerationProvider({ children }: { children: React.ReactNode }) {
  const [active, setActive] = useState<Record<string, ActiveGeneration>>({});
  // One polling loop per project; survives re-renders, cleaned up on unmount
  const timersRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const unmountedRef = useRef(false);

  const stopTracking = useCallback((projectId: string) => {
    const timer = timersRef.current[projectId];
    if (timer) clearTimeout(timer);
    delete timersRef.current[projectId];
    setActive((prev) => {
      const next = { ...prev };
      delete next[projectId];
      return next;
    });
  }, []);

  const track = useCallback((projectId: string, name?: string) => {
    if (timersRef.current[projectId] !== undefined) return; // already tracked

    setActive((prev) => ({
      ...prev,
      [projectId]: {
        projectId,
        name: name || 'your website',
        status: 'generating',
        progress: prev[projectId]?.progress ?? 0,
      },
    }));

    const poll = async () => {
      if (unmountedRef.current) return;
      try {
        const status = await api.generation.getStatus(projectId);
        if (unmountedRef.current) return;

        setActive((prev) => prev[projectId] ? {
          ...prev,
          [projectId]: {
            ...prev[projectId],
            status: (status.status as ActiveGeneration['status']) || 'generating',
            progress: status.progress ?? prev[projectId].progress,
            stage: status.stage ?? prev[projectId].stage,
            stageMessage: status.stage_message ?? prev[projectId].stageMessage,
          },
        } : prev);

        if (status.status === 'completed') {
          toast.success('Website ready!', {
            description: 'Your website finished generating.',
            action: {
              label: 'Open',
              onClick: () => { window.location.href = `/dashboard/projects/${projectId}`; },
            },
            duration: 10000,
          });
          stopTracking(projectId);
          return;
        }
        if (status.status === 'failed') {
          toast.error('Generation failed', {
            description: status.error || 'Something went wrong while building your website.',
            duration: 8000,
          });
          stopTracking(projectId);
          return;
        }
      } catch {
        // transient (auth refresh, network) — keep polling
      }
      timersRef.current[projectId] = setTimeout(poll, POLL_INTERVAL_MS);
    };

    timersRef.current[projectId] = setTimeout(poll, 0);
  }, [stopTracking]);

  // Re-attach on mount: pick up any generation still running server-side
  useEffect(() => {
    unmountedRef.current = false;
    (async () => {
      try {
        const projects = await api.projects.list({ limit: 20, status_filter: 'generating' });
        for (const p of projects || []) {
          track(p.id, p.name);
        }
      } catch {
        // not authenticated yet / transient — pages handle auth redirects
      }
    })();
    const timers = timersRef.current;
    return () => {
      unmountedRef.current = true;
      Object.values(timers).forEach(clearTimeout);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const activeList = Object.values(active);

  return (
    <GenerationContext.Provider value={{ active: activeList, track }}>
      {children}
      <GenerationBanner active={activeList} />
    </GenerationContext.Provider>
  );
}

/** Floating pill(s) showing live progress for in-flight generations */
function GenerationBanner({ active }: { active: ActiveGeneration[] }) {
  const generating = active.filter((a) => a.status === 'generating');
  if (generating.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {generating.map((gen) => (
        <Link
          key={gen.projectId}
          href={`/dashboard/new?project_id=${gen.projectId}`}
          className="flex items-center gap-3 bg-gray-900 text-white rounded-full pl-3 pr-4 py-2 shadow-xl hover:bg-gray-800 transition-colors"
          title={gen.stageMessage || 'Generation in progress'}
        >
          <Loader2 className="w-4 h-4 animate-spin text-indigo-400 shrink-0" />
          <span className="text-xs font-medium truncate max-w-[180px]">
            Building {gen.name}
          </span>
          <span className="text-xs text-indigo-300 font-semibold">{Math.round(gen.progress)}%</span>
        </Link>
      ))}
    </div>
  );
}
