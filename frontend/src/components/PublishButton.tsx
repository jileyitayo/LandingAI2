'use client';

import { useState, useEffect } from 'react';
import { Globe, Loader2, Check, ExternalLink, X } from 'lucide-react';
import { api } from '@/lib/api';

interface PublishButtonProps {
  projectId: string;
  projectName: string;
  deploymentUrl?: string | null;
  isPublished?: boolean;
  onPublishSuccess?: (deploymentUrl: string) => void;
  onUnpublishSuccess?: () => void;
  className?: string;
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
}: PublishButtonProps) {
  const [state, setState] = useState<PublishState>(
    isPublished && deploymentUrl ? 'published' : 'unpublished'
  );
  const [currentUrl, setCurrentUrl] = useState<string | null>(deploymentUrl || null);
  const [error, setError] = useState<string | null>(null);
  const [showUnpublishConfirm, setShowUnpublishConfirm] = useState(false);

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

  const handlePublish = async () => {
    setState('publishing');
    setError(null);

    try {
      const result = await api.deployment.deploy(projectId);
      setCurrentUrl(result.deployment_url);
      setState('published');
      
      // Trigger success callback
      if (onPublishSuccess) {
        onPublishSuccess(result.deployment_url);
      }
    } catch (err: any) {
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
    setShowUnpublishConfirm(false);

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

  // Publishing state
  if (state === 'publishing') {
    return (
      <button
        disabled
        className={`flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg opacity-75 cursor-not-allowed ${className}`}
      >
        <Loader2 className="w-5 h-5 animate-spin" />
        <span>Publishing...</span>
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

  // Published state
  if (state === 'published') {
    return (
      <div className="flex items-center gap-2">
        <button
          onClick={openDeployment}
          className={`flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-medium rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 ${className}`}
          title="Open live site"
        >
          <Check className="w-5 h-5" />
          <span>Published</span>
          <ExternalLink className="w-4 h-4" />
        </button>
        
        {/* Unpublish Button */}
        {showUnpublishConfirm ? (
          <div className="flex items-center gap-2">
            <button
              onClick={handleUnpublish}
              className="px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors text-sm"
            >
              Confirm
            </button>
            <button
              onClick={() => setShowUnpublishConfirm(false)}
              className="px-4 py-2.5 bg-gray-600 hover:bg-gray-700 text-white font-medium rounded-lg transition-colors text-sm"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowUnpublishConfirm(true)}
            className="px-4 py-2.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors text-sm font-medium"
            title="Unpublish site"
          >
            Unpublish
          </button>
        )}
      </div>
    );
  }

  return null;
}

