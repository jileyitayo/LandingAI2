'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import SEOPreview from './SEOPreview';
import DeleteProjectModal from './DeleteProjectModal';
import EditHistoryPanel from './EditHistoryPanel';
import CustomDomainCard from './CustomDomainCard';
import {
  Copy, Check, ExternalLink, Globe, Clock, PencilLine, Files, Loader2, Upload, X,
  FileText, Settings2, Search, History, AlertTriangle,
} from 'lucide-react';

const SECTION_NAV = [
  { id: 'prompt', label: 'Prompt', icon: FileText },
  { id: 'publishing', label: 'Publishing', icon: Globe },
  { id: 'general', label: 'General', icon: Settings2 },
  { id: 'seo', label: 'SEO & Favicon', icon: Search },
  { id: 'history', label: 'Edit History', icon: History },
  { id: 'danger', label: 'Danger Zone', icon: AlertTriangle },
];

interface ProjectSettingsFormProps {
  projectId: string;
  initialData: {
    name: string;
    description?: string;
    prompt?: string;
    subdomain?: string;
    seo_title?: string;
    seo_description?: string;
    favicon_url?: string;
    whatsapp_number?: string;
    published?: boolean;
    deployment_url?: string;
    last_deployed_at?: string;
    last_edited_at?: string;
    created_at?: string;
  };
}

function formatDate(value?: string) {
  if (!value) return '—';
  try {
    const date = new Date(value);
    const day = date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    const time = date
      .toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })
      .toLowerCase();
    return `${day} ${time}`;
  } catch {
    return value;
  }
}

export default function ProjectSettingsForm({
  projectId,
  initialData,
}: ProjectSettingsFormProps) {
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: initialData.name || '',
    seo_title: initialData.seo_title || initialData.name || '',
    seo_description: initialData.seo_description || initialData.description || '',
    favicon_url: initialData.favicon_url || '',
  });

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [promptCopied, setPromptCopied] = useState(false);
  const [urlCopied, setUrlCopied] = useState(false);
  const [duplicating, setDuplicating] = useState(false);
  const [uploadingFavicon, setUploadingFavicon] = useState(false);
  const faviconInputRef = useRef<HTMLInputElement>(null);

  // Track changes
  useEffect(() => {
    const changed =
      formData.name !== (initialData.name || '') ||
      formData.seo_title !== (initialData.seo_title || initialData.name || '') ||
      formData.seo_description !== (initialData.seo_description || initialData.description || '') ||
      formData.favicon_url !== (initialData.favicon_url || '');

    setHasChanges(changed);
  }, [formData, initialData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      setError('Project name is required');
      return;
    }

    setSaving(true);
    setError(null);
    setSaved(false);

    try {
      await api.projects.update(projectId, {
        name: formData.name,
        seo_title: formData.seo_title || undefined,
        seo_description: formData.seo_description || undefined,
        favicon_url: formData.favicon_url || undefined,
      });

      setSaved(true);
      setHasChanges(false);

      // Reset saved message after 3 seconds
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleCopyPrompt = async () => {
    if (!initialData.prompt) return;
    await navigator.clipboard.writeText(initialData.prompt);
    setPromptCopied(true);
    setTimeout(() => setPromptCopied(false), 2000);
  };

  const handleCopyUrl = async () => {
    if (!initialData.deployment_url) return;
    await navigator.clipboard.writeText(initialData.deployment_url);
    setUrlCopied(true);
    setTimeout(() => setUrlCopied(false), 2000);
  };

  const handleDuplicate = async () => {
    setDuplicating(true);
    setError(null);
    try {
      const result = await api.projects.duplicate(projectId);
      const newId = (result as any).id || (result as any).project_id;
      if (newId) {
        router.push(`/dashboard/projects/${newId}`);
      } else {
        router.push('/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to duplicate project');
      setDuplicating(false);
    }
  };

  const handleFaviconUpload = async (file: File | undefined) => {
    if (!file) return;
    setUploadingFavicon(true);
    setError(null);
    try {
      const media = await api.media.upload(file, { projectId, purpose: 'favicon' });
      setFormData((prev) => ({ ...prev, favicon_url: media.public_url }));
    } catch (err: any) {
      setError(err.message || 'Favicon upload failed');
    } finally {
      setUploadingFavicon(false);
      if (faviconInputRef.current) faviconInputRef.current.value = '';
    }
  };

  const handleRevert = async (chatMessageId: string): Promise<boolean> => {
    try {
      await api.generation.revertEdit(projectId, chatMessageId);
      return true;
    } catch (err: any) {
      setError(err.message || 'Revert failed');
      return false;
    }
  };

  return (
    <div className="space-y-8">
      {/* Quick section navigation */}
      <nav className="sticky top-0 z-10 -mx-1 bg-gray-50/95 backdrop-blur px-1 py-2">
        <div className="flex flex-wrap gap-2">
          {SECTION_NAV.filter((s) => s.id !== 'prompt' || initialData.prompt).map((section) => (
            <a
              key={section.id}
              href={`#${section.id}`}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                section.id === 'danger'
                  ? 'border-red-200 text-red-600 hover:bg-red-50'
                  : 'border-gray-200 text-gray-600 hover:bg-white hover:text-gray-900'
              }`}
            >
              <section.icon className="w-3.5 h-3.5" />
              {section.label}
            </a>
          ))}
        </div>
      </nav>

      {/* Original Generation Prompt */}
      {initialData.prompt && (
        <div id="prompt" className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg scroll-mt-16">
          <div className="px-4 py-6 sm:p-8">
            <div className="max-w-2xl space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="flex items-center gap-2 text-base font-semibold leading-7 text-gray-900">
                    <FileText className="w-4 h-4 text-indigo-500" />
                    Original Prompt
                  </h2>
                  <p className="mt-1 text-sm leading-6 text-gray-600">
                    The prompt used to generate this website{initialData.created_at ? ` on ${formatDate(initialData.created_at)}` : ''}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleCopyPrompt}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  {promptCopied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                  {promptCopied ? 'Copied' : 'Copy'}
                </button>
              </div>
              <blockquote className="rounded-md bg-gray-50 border border-gray-200 p-4 text-sm text-gray-700 whitespace-pre-wrap">
                {initialData.prompt}
              </blockquote>
            </div>
          </div>
        </div>
      )}

      {/* Publishing */}
      <div id="publishing" className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg scroll-mt-16">
        <div className="px-4 py-6 sm:p-8">
          <div className="max-w-2xl space-y-4">
            <h2 className="flex items-center gap-2 text-base font-semibold leading-7 text-gray-900">
              <Globe className="w-4 h-4 text-green-600" />
              Publishing
            </h2>
            <div className="flex items-center gap-2">
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  initialData.published
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                <Globe className="w-3 h-3" />
                {initialData.published ? 'Live' : 'Not published'}
              </span>
            </div>

            {initialData.deployment_url && (
              <div className="flex items-center gap-2 rounded-md bg-gray-50 border border-gray-200 px-3 py-2">
                <a
                  href={initialData.deployment_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 truncate text-sm text-indigo-600 hover:text-indigo-800"
                >
                  {initialData.deployment_url}
                </a>
                <button
                  type="button"
                  onClick={handleCopyUrl}
                  className="p-1.5 text-gray-500 hover:text-gray-800 rounded transition-colors"
                  title="Copy URL"
                >
                  {urlCopied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                </button>
                <a
                  href={initialData.deployment_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 text-gray-500 hover:text-gray-800 rounded transition-colors"
                  title="Open live site"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            )}

            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div className="flex items-center gap-2 text-gray-600">
                <Clock className="w-4 h-4 text-gray-400" />
                <dt>Last published:</dt>
                <dd className="text-gray-900">{formatDate(initialData.last_deployed_at)}</dd>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <PencilLine className="w-4 h-4 text-gray-400" />
                <dt>Last edited:</dt>
                <dd className="text-gray-900">{formatDate(initialData.last_edited_at)}</dd>
              </div>
            </dl>
            <p className="text-xs text-gray-500">
              Publishing and unpublishing are done from the editor's Publish button.
            </p>

            <CustomDomainCard projectId={projectId} published={!!initialData.published} />
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* General Settings */}
        <div id="general" className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg scroll-mt-16">
          <div className="px-4 py-6 sm:p-8">
            <div className="max-w-2xl space-y-6">
              <div>
                <h2 className="flex items-center gap-2 text-base font-semibold leading-7 text-gray-900">
                  <Settings2 className="w-4 h-4 text-gray-500" />
                  General Settings
                </h2>
                <p className="mt-1 text-sm leading-6 text-gray-600">
                  Basic information about your project
                </p>
              </div>

              {/* Project Name */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Project Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
                  maxLength={200}
                  required
                />
                <p className="mt-1 text-xs text-gray-500">{formData.name.length}/200 characters</p>
              </div>
            </div>
          </div>
        </div>

        {/* SEO Settings */}
        <div id="seo" className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg scroll-mt-16">
          <div className="px-4 py-6 sm:p-8">
            <div className="max-w-2xl space-y-6">
              <div>
                <h2 className="flex items-center gap-2 text-base font-semibold leading-7 text-gray-900">
                  <Search className="w-4 h-4 text-blue-500" />
                  SEO &amp; Site Identity
                </h2>
                <p className="mt-1 text-sm leading-6 text-gray-600">
                  How your site appears in search results and browser tabs. Applied on the next publish.
                </p>
              </div>

              {/* SEO Title */}
              <div>
                <label htmlFor="seo_title" className="block text-sm font-medium text-gray-700">
                  SEO Title
                </label>
                <input
                  type="text"
                  id="seo_title"
                  value={formData.seo_title}
                  onChange={(e) => setFormData({ ...formData, seo_title: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
                  maxLength={60}
                  placeholder={formData.name}
                />
                <p className="mt-1 text-xs text-gray-500">{formData.seo_title.length}/60 characters</p>
              </div>

              {/* SEO Description */}
              <div>
                <label
                  htmlFor="seo_description"
                  className="block text-sm font-medium text-gray-700"
                >
                  SEO Description
                </label>
                <textarea
                  id="seo_description"
                  rows={3}
                  value={formData.seo_description}
                  onChange={(e) => setFormData({ ...formData, seo_description: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
                  maxLength={160}
                  placeholder={initialData.description}
                />
                <p className="mt-1 text-xs text-gray-500">{formData.seo_description.length}/160 characters</p>
              </div>

              {/* Favicon */}
              <div>
                <label className="block text-sm font-medium text-gray-700">Favicon</label>
                <div className="mt-1 flex items-center gap-3">
                  {formData.favicon_url ? (
                    <div className="relative">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={formData.favicon_url}
                        alt="Favicon"
                        className="w-10 h-10 rounded border border-gray-200 object-cover"
                      />
                      <button
                        type="button"
                        onClick={() => setFormData({ ...formData, favicon_url: '' })}
                        className="absolute -top-1.5 -right-1.5 bg-gray-700 text-white rounded-full p-0.5 hover:bg-gray-900"
                        title="Remove favicon"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ) : (
                    <div className="w-10 h-10 rounded border border-dashed border-gray-300 flex items-center justify-center text-gray-400 text-xs">
                      —
                    </div>
                  )}
                  <input
                    ref={faviconInputRef}
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    className="hidden"
                    onChange={(e) => handleFaviconUpload(e.target.files?.[0])}
                  />
                  <button
                    type="button"
                    onClick={() => faviconInputRef.current?.click()}
                    disabled={uploadingFavicon}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
                  >
                    {uploadingFavicon ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Upload className="w-4 h-4" />
                    )}
                    {uploadingFavicon ? 'Uploading…' : 'Upload favicon'}
                  </button>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Square PNG recommended (32×32 or larger). Shown in browser tabs after the next publish.
                </p>
              </div>

              {/* SEO Preview */}
              <SEOPreview
                title={formData.seo_title}
                description={formData.seo_description}
                subdomain={initialData.subdomain || ''}
              />
            </div>
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex items-center justify-between">
          <div>
            {error && (
              <div className="text-sm text-red-600 flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                {error}
              </div>
            )}
            {saved && (
              <div className="text-sm text-green-600 flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                Settings saved successfully!
              </div>
            )}
          </div>
          <button
            type="submit"
            disabled={saving || !hasChanges}
            className="inline-flex justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>

      {/* Edit History */}
      <div id="history" className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg scroll-mt-16">
        <div className="px-4 py-6 sm:p-8">
          <div className="max-w-2xl space-y-4">
            <div>
              <h2 className="flex items-center gap-2 text-base font-semibold leading-7 text-gray-900">
                <History className="w-4 h-4 text-purple-500" />
                Edit History
              </h2>
              <p className="mt-1 text-sm leading-6 text-gray-600">
                Every AI edit made to this project, with one-click revert
              </p>
            </div>
            <div className="bg-gray-900 rounded-lg max-h-96 overflow-hidden flex flex-col">
              <EditHistoryPanel projectId={projectId} onRevert={handleRevert} />
            </div>
          </div>
        </div>
      </div>

      {/* Duplicate */}
      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg">
        <div className="px-4 py-6 sm:p-8">
          <div className="max-w-2xl flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold leading-7 text-gray-900">Duplicate Project</h2>
              <p className="mt-1 text-sm leading-6 text-gray-600">
                Create a copy of this project, including all files and the original prompt
              </p>
            </div>
            <button
              type="button"
              onClick={handleDuplicate}
              disabled={duplicating}
              className="inline-flex items-center gap-2 justify-center rounded-md bg-white px-4 py-2 text-sm font-semibold text-gray-700 shadow-sm border border-gray-300 hover:bg-gray-50 disabled:opacity-50"
            >
              {duplicating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Files className="w-4 h-4" />}
              {duplicating ? 'Duplicating…' : 'Duplicate'}
            </button>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div id="danger" className="bg-white shadow-sm ring-1 ring-red-900/10 sm:rounded-lg border-red-200 border scroll-mt-16">
        <div className="px-4 py-6 sm:p-8">
          <div className="max-w-2xl">
            <h2 className="flex items-center gap-2 text-base font-semibold leading-7 text-red-900">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              Danger Zone
            </h2>
            <p className="mt-1 text-sm leading-6 text-red-600 mb-4">
              Irreversible and destructive actions
            </p>
            <button
              type="button"
              onClick={() => setShowDeleteModal(true)}
              className="inline-flex justify-center rounded-md bg-red-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600"
            >
              Delete Project
            </button>
          </div>
        </div>
      </div>

      {/* Delete Modal */}
      <DeleteProjectModal
        projectId={projectId}
        projectName={formData.name}
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
      />
    </div>
  );
}
