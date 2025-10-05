'use client';

import { useRouter } from 'next/navigation';
import { Calendar, Edit, Trash2 } from 'lucide-react';
import { Project } from '@/types/project.types';

interface ProjectCardProps {
  project: Project;
  onDelete?: (id: string) => void;
}

export default function ProjectCard({ project, onDelete }: ProjectCardProps) {
  const router = useRouter();

  const handleEdit = () => {
    router.push(`/dashboard/projects/${project.id}`);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete && confirm('Are you sure you want to delete this project?')) {
      onDelete(project.id);
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

  return (
    <div
      className="bg-white rounded-lg border border-gray-200 hover:border-blue-500 transition-all cursor-pointer group"
      onClick={handleEdit}
    >
      {/* Preview Thumbnail */}
      <div className="h-40 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-t-lg flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity bg-black/10 flex items-center justify-center">
          <div className="bg-white rounded-full p-3 shadow-lg">
            <Edit className="w-5 h-5 text-blue-600" />
          </div>
        </div>
        {project.preview_url ? (
          <img
            src={project.preview_url}
            alt={project.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="text-6xl font-bold text-blue-200">
            {project.name.charAt(0).toUpperCase()}
          </div>
        )}
      </div>

      {/* Project Info */}
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-1 truncate">
          {project.name}
        </h3>
        {project.description && (
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">
            {project.description}
          </p>
        )}

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Calendar className="w-3 h-3" />
            <span>{formatDate(project.updated_at)}</span>
          </div>

          <button
            onClick={handleDelete}
            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
            title="Delete project"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>

        {project.is_published && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Published
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

