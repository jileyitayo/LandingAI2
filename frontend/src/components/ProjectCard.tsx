'use client';

import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { Calendar, Edit, Trash2, Copy, ExternalLink, Loader2 } from 'lucide-react';
import { Project } from '@/types/project.types';
import { useState } from 'react';
import { useActiveGenerations } from '@/contexts/GenerationContext';

// Blur placeholder for image loading
const shimmer = (w: number, h: number) => `
<svg width="${w}" height="${h}" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <defs>
    <linearGradient id="g">
      <stop stop-color="#e0e7ff" offset="20%" />
      <stop stop-color="#c7d2fe" offset="50%" />
      <stop stop-color="#e0e7ff" offset="70%" />
    </linearGradient>
  </defs>
  <rect width="${w}" height="${h}" fill="#e0e7ff" />
  <rect id="r" width="${w}" height="${h}" fill="url(#g)" />
  <animate xlink:href="#r" attributeName="x" from="-${w}" to="${w}" dur="1s" repeatCount="indefinite"  />
</svg>`;

const toBase64 = (str: string) =>
  typeof window === 'undefined'
    ? Buffer.from(str).toString('base64')
    : window.btoa(str);

interface ProjectCardProps {
  project: Project;
  onDelete?: (id: string) => void;
  onDuplicate?: (id: string) => void;
}

export default function ProjectCard({ project, onDelete, onDuplicate }: ProjectCardProps) {
  const router = useRouter();
  const [isDeleting, setIsDeleting] = useState(false);
  const [isDuplicating, setIsDuplicating] = useState(false);
  const [imageError, setImageError] = useState(false);

  // Live progress for an in-flight generation (dashboard-wide tracker)
  const generations = useActiveGenerations();
  const liveGeneration = generations?.active.find(
    (g) => g.projectId === project.id && g.status === 'generating'
  );
  const isGenerating = !!liveGeneration || project.generation_status === 'generating';

  const handleEdit = () => {
    // A generating project has no files to edit yet — open the progress view
    if (isGenerating) {
      router.push(`/dashboard/new?project_id=${project.id}`);
      return;
    }
    router.push(`/dashboard/projects/${project.id}`);
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isDeleting) return;

    if (confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      setIsDeleting(true);
      try {
        if (onDelete) {
          await onDelete(project.id);
        }
      } catch (error) {
        console.error('Failed to delete project:', error);
      } finally {
        setIsDeleting(false);
      }
    }
  };

  const handleDuplicate = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isDuplicating) return;

    setIsDuplicating(true);
    try {
      if (onDuplicate) {
        await onDuplicate(project.id);
      }
    } catch (error) {
      console.error('Failed to duplicate project:', error);
    } finally {
      setIsDuplicating(false);
    }
  };

  const handleViewLive = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (project.preview_url) {
      window.open(project.preview_url, '_blank');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getStatusBadge = () => {
    if (isGenerating) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
          <Loader2 className="w-3 h-3 animate-spin" />
          Generating{liveGeneration ? ` ${Math.round(liveGeneration.progress)}%` : ''}
        </span>
      );
    }
    // If project has preview_url or is_published, it's completed
    if (project.is_published || project.preview_url) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <div className="w-1.5 h-1.5 rounded-full bg-green-600"></div>
          Published
        </span>
      );
    }
    return null;
  };

  return (
    <div
      className="bg-white rounded-lg border border-gray-200 hover:border-indigo-400 hover:shadow-lg transition-all duration-200 cursor-pointer group overflow-hidden"
      onClick={handleEdit}
    >
      {/* Preview Thumbnail */}
      <div className="h-48 bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 relative overflow-hidden">
        {project.thumbnail_url && !imageError ? (
          <>
            <Image
              src={project.thumbnail_url}
              alt={project.name}
              fill
              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
              className="object-cover"
              priority={false}
              loading="lazy"
              quality={75}
              placeholder="blur"
              blurDataURL={`data:image/svg+xml;base64,${toBase64(shimmer(700, 475))}`}
              onError={() => setImageError(true)}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl font-bold text-indigo-200 mb-2">
                {project.name.charAt(0).toUpperCase()}
              </div>
              <div className="text-sm text-indigo-300 font-medium">
                {project.name}
              </div>
            </div>
          </div>
        )}

        {/* Hover Overlay with Edit Button */}
        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          <div className="bg-white rounded-full p-3 shadow-xl transform scale-90 group-hover:scale-100 transition-transform">
            <Edit className="w-6 h-6 text-indigo-600" />
          </div>
        </div>

        {/* Status Badge */}
        {getStatusBadge() && (
          <div className="absolute top-3 right-3">
            {getStatusBadge()}
          </div>
        )}

        {/* Live generation progress */}
        {liveGeneration && (
          <div className="absolute bottom-0 left-0 right-0">
            <div className="h-1.5 bg-black/10">
              <div
                className="h-full bg-indigo-500 transition-[width] duration-500"
                style={{ width: `${Math.max(3, Math.round(liveGeneration.progress))}%` }}
              />
            </div>
            {liveGeneration.stageMessage && (
              <div className="bg-black/50 text-white text-[11px] px-3 py-1 truncate">
                {liveGeneration.stageMessage}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Project Info */}
      <div className="p-5">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 truncate group-hover:text-indigo-600 transition-colors">
          {project.name}
        </h3>
        
        {project.description && (
          <p className="text-sm text-gray-600 mb-4 line-clamp-2 min-h-[40px]">
            {project.description}
          </p>
        )}

        {/* Meta Information */}
        <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
          <div className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            <span>Updated {formatDate(project.updated_at)}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 pt-4 border-t border-gray-100">
          {/* View Live Button */}
          {project.is_published && project.preview_url && (
            <button
              onClick={handleViewLive}
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors"
              title="View live site"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              View Live
            </button>
          )}

          {/* Duplicate Button */}
          <button
            onClick={handleDuplicate}
            disabled={isDuplicating}
            className="inline-flex items-center justify-center p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Duplicate project"
          >
            {isDuplicating ? (
              <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>

          {/* Delete Button */}
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="inline-flex items-center justify-center p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Delete project"
          >
            {isDeleting ? (
              <div className="w-4 h-4 border-2 border-red-600 border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <Trash2 className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
