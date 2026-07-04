'use client';

import { useState, useEffect } from 'react';
import { Globe, Loader2, Check, ExternalLink, X, RefreshCw, ChevronDown } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';

interface PublishButtonProps {
  projectId: string;
  projectName: string;
  deploymentUrl?: string | null;
  isPublished?: boolean;
  onPublishSuccess?: (deploymentUrl: string) => void;
  onUnpublishSuccess?: () => void;
  className?: string;
  // Bump to re-check for unpublished changes (e.g. after each successful edit)
  editVersion?: number;
}

type PublishState = 'unpublished' | 'publishing' | 'published' | 'unpublishing' | 'error';

export default function PublishButton({
  projectId,
  projectName,
  deploymentUrl,
  isPublished = false,
  onPublishSuccess,
  onUnpublishSuccess,
  className = '',
  editVersion = 0,
}: PublishButtonProps) {
  const [state, setState] = useState<PublishState>(
    isPublished && deploymentUrl ? 'published' : 'unpublished'
  );
  const [currentUrl, setCurrentUrl] = useState<string | null>(deploymentUrl || null);
  const [error, setError] = useState<string | null>(null);
  const [hasUnpublishedChanges, setHasUnpublishedChanges] = useState(false);
  const [deployStage, setDeployStage] = useState<string>('queued');
  const [menuOpen, setMenuOpen] = useState(false);

  // Close the dropdown on outside click
  useEffect(() => {
    if (!menuOpen) return;
    const close = () => setMenuOpen(false);
    // Defer so the toggling click doesn't immediately close it
    const timer = setTimeout(() => document.addEventListener('click', close), 0);
    return () => {
      clearTimeout(timer);
      document.removeEventListener('click', close);
    };
  }, [menuOpen]);

  // Update state when props change
  useEffect(() => {
    if (isPublished && deploymentUrl) {
      setState('published');
      setCurrentUrl(deploymentUrl);
    } else {
      setState('unpublished');
      setCurrentUrl(null);
    }
  }, [isPublished, deploymentUrl]);

  // Poll deployment progress while a deploy is in flight. Deploys run as a
  // backend background task, so this also resumes after a page reload.
  useEffect(() => {
    if (state !== 'publishing') return;
    let cancelled = false;

    const poll = async () => {
      try {
        const status = await api.deployment.getStatus(projectId);
        if (cancelled) return;

        if (status.deploy_status === 'ready') {
          setCurrentUrl(status.deployment_url);
          setState('published');
          setHasUnpublishedChanges(false);
          toast.success('Your site is live! 🎉', {
            description: status.deployment_url || undefined,
            duration: 6000,
            action: status.deployment_url
              ? { label: 'Open', onClick: () => window.open(status.deployment_url!, '_blank', 'noopener,noreferrer') }
              : undefined,
          });
          if (status.deployment_url && onPublishSuccess) {
            onPublishSuccess(status.deployment_url);
          }
          return;
        }
        if (status.deploy_status === 'error') {
          setState('error');
          setError(status.deploy_error || 'Deployment failed. Please try again.');
          toast.error('Publish failed', {
            description: status.deploy_error || 'Deployment failed. Please try again.',
            duration: 8000,
          });
          setTimeout(() => {
            if (!cancelled) {
              setState(isPublished && deploymentUrl ? 'published' : 'unpublished');
              setError(null);
            }
          }, 5000);
          return;
        }
        setDeployStage(status.deploy_status);
        setTimeout(poll, 3000);
      } catch {
        if (!cancelled) setTimeout(poll, 5000);
      }
    };

    poll();
    return () => {
      cancelled = true;
    };
  }, [state, projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Check whether the live site is behind the latest edits, and resume
  // progress display if a deploy is already running (e.g. after reload)
  useEffect(() => {
    let cancelled = false;
    api.deployment
      .getStatus(projectId)
      .then((status) => {
        if (cancelled) return;
        if (['queued', 'uploading', 'building'].includes(status.deploy_status) && state !== 'publishing') {
          setDeployStage(status.deploy_status);
          setState('publishing');
          return;
        }
        if (isPublished) {
          setHasUnpublishedChanges(Boolean(status.has_unpublished_changes));
        } else {
          setHasUnpublishedChanges(false);
        }
      })
      .catch(() => {
        /* badge is best-effort; ignore status errors */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, isPublished, editVersion, state]); // eslint-disable-line react-hooks/exhaustive-deps

  const handlePublish = async () => {
    setError(null);
    setDeployStage('queued');

    try {
      await api.deployment.deploy(projectId);
      setState('publishing');
    } catch (err: any) {
      // 409 = a deploy is already running: just show its progress
      if (err?.status === 409) {
        setState('publishing');
        return;
      }
      console.error('Publish error:', err);
      setState('error');
      setError(err.message || 'Failed to publish. Please try again.');

      // Reset to unpublished after showing error
      setTimeout(() => {
        if (isPublished && deploymentUrl) {
          setState('published');
          setCurrentUrl(deploymentUrl);
        } else {
          setState('unpublished');
        }
        setError(null);
      }, 3000);
    }
  };

  const handleUnpublish = async () => {
    setState('unpublishing');
    setError(null);

    try {
      await api.deployment.deleteDeployment(projectId);
      setCurrentUrl(null);
      setState('unpublished');
      
      // Trigger success callback
      if (onUnpublishSuccess) {
        onUnpublishSuccess();
      }
    } catch (err: any) {
      console.error('Unpublish error:', err);
      setState('error');
      setError(err.message || 'Failed to unpublish. Please try again.');
      
      // Reset to published after showing error
      setTimeout(() => {
        setState('published');
        setError(null);
      }, 3000);
    }
  };

  const openDeployment = () => {
    if (currentUrl) {
      window.open(currentUrl, '_blank', 'noopener,noreferrer');
    }
  };

  // Unpublished state
  if (state === 'unpublished') {
    return (
      <button
        onClick={handlePublish}
        className={`flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 ${className}`}
      >
        <Globe className="w-5 h-5" />
        <span>Publish Live</span>
      </button>
    );
  }

  // Publishing state — staged progress from the async deploy
  if (state === 'publishing') {
    const stageLabels: Record<string, string> = {
      queued: 'Queued…',
      uploading: 'Uploading files…',
      building: 'Building site…',
    };
    const stages = ['queued', 'uploading', 'building'];
    const activeIndex = Math.max(stages.indexOf(deployStage), 0);
    return (
      <button
        disabled
        className={`flex items-center gap-2.5 px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg opacity-90 cursor-wait ${className}`}
        title="Deployment runs in the background — you can keep editing"
      >
        <Loader2 className="w-5 h-5 animate-spin" />
        <span>{stageLabels[deployStage] || 'Publishing…'}</span>
        <span className="flex items-center gap-1">
          {stages.map((s, i) => (
            <span
              key={s}
              className={`w-1.5 h-1.5 rounded-full ${
                i < activeIndex ? 'bg-white' : i === activeIndex ? 'bg-white animate-pulse' : 'bg-white/30'
              }`}
            />
          ))}
        </span>
      </button>
    );
  }

  // Unpublishing state
  if (state === 'unpublishing') {
    return (
      <button
        disabled
        className={`flex items-center gap-2 px-6 py-2.5 bg-gray-600 text-white font-medium rounded-lg opacity-75 cursor-not-allowed ${className}`}
      >
        <Loader2 className="w-5 h-5 animate-spin" />
        <span>Unpublishing...</span>
      </button>
    );
  }

  // Error state
  if (state === 'error') {
    return (
      <button
        disabled
        className={`flex items-center gap-2 px-6 py-2.5 bg-red-600 text-white font-medium rounded-lg opacity-75 cursor-not-allowed ${className}`}
      >
        <X className="w-5 h-5" />
        <span className="truncate max-w-[200px]">{error || 'Error'}</span>
      </button>
    );
  }

  // Published state — one split button: main action + dropdown menu
  if (state === 'published') {
    return (
      <div className={`relative ${className}`}>
        <div className="flex items-stretch rounded-lg overflow-hidden shadow-lg">
          {hasUnpublishedChanges ? (
            <button
              onClick={handlePublish}
              className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-medium transition-colors"
              title="Your latest edits aren't live yet — click to publish them"
            >
              <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
              <span>Publish changes</span>
            </button>
          ) : (
            <button
              onClick={openDeployment}
              className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-medium transition-colors"
              title="Open live site"
            >
              <Check className="w-5 h-5" />
              <span>Published</span>
              <ExternalLink className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => setMenuOpen((prev) => !prev)}
            className={`flex items-center px-2 border-l transition-colors text-white ${
              hasUnpublishedChanges
                ? 'bg-orange-500 hover:bg-orange-600 border-orange-400/50'
                : 'bg-emerald-600 hover:bg-emerald-700 border-emerald-500/50'
            }`}
            title="Publishing options"
            aria-label="Publishing options"
          >
            <ChevronDown className={`w-4 h-4 transition-transform ${menuOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {menuOpen && (
          <div
            className="absolute right-0 mt-2 w-56 bg-gray-800 border border-gray-700 rounded-lg shadow-xl py-1 z-50"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => {
                setMenuOpen(false);
                openDeployment();
              }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-200 hover:bg-gray-700 transition-colors"
            >
              <ExternalLink className="w-4 h-4 text-gray-400" />
              Open live site
            </button>
            <button
              onClick={() => {
                setMenuOpen(false);
                handlePublish();
              }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-200 hover:bg-gray-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4 text-gray-400" />
              {hasUnpublishedChanges ? 'Publish latest changes' : 'Republish'}
            </button>
            <div className="my-1 border-t border-gray-700" />
            <button
              onClick={() => {
                setMenuOpen(false);
                if (window.confirm('Take your site offline? Visitors will no longer be able to access it.')) {
                  handleUnpublish();
                }
              }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-gray-700 transition-colors"
            >
              <X className="w-4 h-4" />
              Unpublish
            </button>
          </div>
        )}
      </div>
    );
  }

  return null;
}

