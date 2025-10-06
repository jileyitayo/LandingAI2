'use client';

import { useState, useEffect } from 'react';
import { Clock, ExternalLink, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

interface DeploymentHistoryProps {
  projectId: string;
  className?: string;
}

interface DeploymentStatus {
  deployment_id: string | null;
  deployment_url: string | null;
  state: string;
  ready: boolean;
  last_deployed_at: string | null;
}

export default function DeploymentHistory({
  projectId,
  className = '',
}: DeploymentHistoryProps) {
  const [status, setStatus] = useState<DeploymentStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDeploymentStatus();
  }, [projectId]);

  const fetchDeploymentStatus = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await api.deployment.getStatus(projectId);
      setStatus(data);
    } catch (err: any) {
      console.error('Failed to fetch deployment status:', err);
      setError(err.message || 'Failed to load deployment history');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    });
  };

  const getStateColor = (state: string) => {
    switch (state.toLowerCase()) {
      case 'ready':
      case 'success':
        return 'text-green-600 bg-green-50';
      case 'building':
      case 'queued':
        return 'text-blue-600 bg-blue-50';
      case 'error':
      case 'failed':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getStateIcon = (state: string, ready: boolean) => {
    if (ready) {
      return <CheckCircle2 className="w-4 h-4 text-green-600" />;
    }
    
    switch (state.toLowerCase()) {
      case 'building':
      case 'queued':
        return <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'error':
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-600" />;
    }
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
        <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Clock className="w-4 h-4" />
          Deployment Status
        </h3>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 text-gray-400 animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
        <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Clock className="w-4 h-4" />
          Deployment Status
        </h3>
        <div className="flex items-center gap-2 text-sm text-red-600 py-4">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (!status || !status.deployment_id) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
        <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Clock className="w-4 h-4" />
          Deployment Status
        </h3>
        <p className="text-sm text-gray-500 py-4">
          No deployments yet. Click "Publish Live" to deploy your site.
        </p>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
        <Clock className="w-4 h-4" />
        Deployment Status
      </h3>

      <div className="space-y-3">
        {/* Current Deployment */}
        <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
          <div className="flex-shrink-0 mt-0.5">
            {getStateIcon(status.state, status.ready)}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={`text-xs font-medium px-2 py-1 rounded-full ${getStateColor(status.state)}`}>
                {status.state.charAt(0).toUpperCase() + status.state.slice(1)}
              </span>
            </div>
            
            {status.deployment_url && (
              <a
                href={status.deployment_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-700 hover:underline flex items-center gap-1 mb-1"
              >
                <span className="truncate">{status.deployment_url}</span>
                <ExternalLink className="w-3 h-3 flex-shrink-0" />
              </a>
            )}
            
            <p className="text-xs text-gray-500">
              {status.last_deployed_at ? (
                <>Deployed {formatDate(status.last_deployed_at)}</>
              ) : (
                'Deployment pending'
              )}
            </p>
          </div>
        </div>

        {/* Deployment ID */}
        {status.deployment_id && (
          <div className="flex items-center justify-between text-xs text-gray-500 px-3">
            <span>Deployment ID:</span>
            <code className="bg-gray-100 px-2 py-1 rounded font-mono">
              {status.deployment_id.slice(0, 12)}...
            </code>
          </div>
        )}
      </div>
    </div>
  );
}

