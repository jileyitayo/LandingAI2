/**
 * DeploymentButton Component - Example
 * 
 * This is an example component demonstrating how to integrate
 * the Vercel deployment API into your frontend.
 * 
 * Features:
 * - Deploy project to Vercel
 * - Show deployment status
 * - Handle loading and error states
 * - Display deployment URL
 * - Delete deployment
 */

'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface DeploymentButtonProps {
  projectId: string;
  projectName: string;
  hasContent: boolean;
  initialDeploymentUrl?: string | null;
  initialDeploymentId?: string | null;
  onDeploymentChange?: (deploymentUrl: string | null) => void;
}

export function DeploymentButton({
  projectId,
  projectName,
  hasContent,
  initialDeploymentUrl = null,
  initialDeploymentId = null,
  onDeploymentChange,
}: DeploymentButtonProps) {
  const [isDeploying, setIsDeploying] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deploymentUrl, setDeploymentUrl] = useState<string | null>(initialDeploymentUrl);
  const [deploymentId, setDeploymentId] = useState<string | null>(initialDeploymentId);
  const [error, setError] = useState<string | null>(null);
  const [deploymentStatus, setDeploymentStatus] = useState<string>('NOT_DEPLOYED');

  // Fetch deployment status on mount if deployment exists
  useEffect(() => {
    if (deploymentId) {
      fetchDeploymentStatus();
    }
  }, [deploymentId]);

  const fetchDeploymentStatus = async () => {
    try {
      const status = await api.deployment.getStatus(projectId);
      setDeploymentStatus(status.state);
      if (status.deployment_url) {
        setDeploymentUrl(status.deployment_url);
      }
    } catch (err: any) {
      console.error('Failed to fetch deployment status:', err);
    }
  };

  const handleDeploy = async () => {
    // Clear any previous errors
    setError(null);
    setIsDeploying(true);

    try {
      const result = await api.deployment.deploy(projectId);
      
      // Update state with deployment information
      setDeploymentUrl(result.deployment_url);
      setDeploymentId(result.deployment_id);
      setDeploymentStatus('READY');
      
      // Notify parent component
      if (onDeploymentChange) {
        onDeploymentChange(result.deployment_url);
      }

      // Show success message
      alert(`Successfully deployed to ${result.deployment_url}`);
    } catch (err: any) {
      console.error('Deployment failed:', err);
      setError(err.message || 'Failed to deploy project');
    } finally {
      setIsDeploying(false);
    }
  };

  const handleDeleteDeployment = async () => {
    if (!confirm('Are you sure you want to delete this deployment? The website will no longer be accessible.')) {
      return;
    }

    setError(null);
    setIsDeleting(true);

    try {
      await api.deployment.deleteDeployment(projectId);
      
      // Clear deployment information
      setDeploymentUrl(null);
      setDeploymentId(null);
      setDeploymentStatus('NOT_DEPLOYED');
      
      // Notify parent component
      if (onDeploymentChange) {
        onDeploymentChange(null);
      }

      alert('Deployment deleted successfully');
    } catch (err: any) {
      console.error('Failed to delete deployment:', err);
      setError(err.message || 'Failed to delete deployment');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleRefreshStatus = async () => {
    await fetchDeploymentStatus();
  };

  // Render deployment status badge
  const renderStatusBadge = () => {
    const statusColors: Record<string, string> = {
      'READY': 'bg-green-100 text-green-800',
      'BUILDING': 'bg-yellow-100 text-yellow-800',
      'ERROR': 'bg-red-100 text-red-800',
      'NOT_DEPLOYED': 'bg-gray-100 text-gray-800',
    };

    const color = statusColors[deploymentStatus] || statusColors['NOT_DEPLOYED'];

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded ${color}`}>
        {deploymentStatus.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div className="space-y-4">
      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Deployment Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-700">Deployment Status:</span>
          {renderStatusBadge()}
        </div>
        
        {deploymentId && (
          <button
            onClick={handleRefreshStatus}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            Refresh Status
          </button>
        )}
      </div>

      {/* Deployment URL */}
      {deploymentUrl && (
        <div className="bg-blue-50 border border-blue-200 rounded p-4">
          <p className="text-sm text-gray-600 mb-2">Your website is live at:</p>
          <a
            href={deploymentUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-700 font-medium break-all"
          >
            {deploymentUrl}
          </a>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex space-x-3">
        {!deploymentUrl ? (
          <button
            onClick={handleDeploy}
            disabled={isDeploying || !hasContent}
            className={`
              px-4 py-2 rounded font-medium
              ${isDeploying || !hasContent
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
              }
            `}
          >
            {isDeploying ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Deploying...
              </span>
            ) : (
              'Deploy to Vercel'
            )}
          </button>
        ) : (
          <>
            <button
              onClick={handleDeploy}
              disabled={isDeploying}
              className="px-4 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500"
            >
              {isDeploying ? 'Redeploying...' : 'Redeploy'}
            </button>
            
            <button
              onClick={handleDeleteDeployment}
              disabled={isDeleting}
              className="px-4 py-2 bg-red-600 text-white rounded font-medium hover:bg-red-700 disabled:bg-gray-300 disabled:text-gray-500"
            >
              {isDeleting ? 'Deleting...' : 'Delete Deployment'}
            </button>
          </>
        )}
      </div>

      {/* Help Text */}
      {!hasContent && (
        <p className="text-sm text-gray-500">
          Generate or add content to your project before deploying.
        </p>
      )}
    </div>
  );
}

/**
 * Usage Example:
 * 
 * ```tsx
 * import { DeploymentButton } from '@/components/DeploymentButton';
 * 
 * function ProjectPage({ project }) {
 *   return (
 *     <div>
 *       <h1>{project.name}</h1>
 *       
 *       <DeploymentButton
 *         projectId={project.id}
 *         projectName={project.name}
 *         hasContent={!!project.html_content}
 *         initialDeploymentUrl={project.deployment_url}
 *         initialDeploymentId={project.deployment_id}
 *         onDeploymentChange={(url) => {
 *           console.log('Deployment changed:', url);
 *         }}
 *       />
 *     </div>
 *   );
 * }
 * ```
 * 
 * Alternative: Using with React Query
 * 
 * ```tsx
 * import { useQuery, useMutation } from '@tanstack/react-query';
 * import { api } from '@/lib/api';
 * 
 * function DeploymentSection({ projectId }) {
 *   // Query for deployment status
 *   const { data: status, refetch } = useQuery({
 *     queryKey: ['deployment-status', projectId],
 *     queryFn: () => api.deployment.getStatus(projectId),
 *     refetchInterval: 5000, // Refetch every 5 seconds if building
 *   });
 * 
 *   // Mutation for deploying
 *   const deployMutation = useMutation({
 *     mutationFn: () => api.deployment.deploy(projectId),
 *     onSuccess: () => {
 *       refetch();
 *     },
 *   });
 * 
 *   // Mutation for deleting
 *   const deleteMutation = useMutation({
 *     mutationFn: () => api.deployment.deleteDeployment(projectId),
 *     onSuccess: () => {
 *       refetch();
 *     },
 *   });
 * 
 *   return (
 *     <div>
 *       <button onClick={() => deployMutation.mutate()}>
 *         Deploy
 *       </button>
 *       
 *       {status?.deployment_url && (
 *         <a href={status.deployment_url} target="_blank">
 *           Visit Site
 *         </a>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */

