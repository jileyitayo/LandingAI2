'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import SubdomainInput from './SubdomainInput';
import SEOPreview from './SEOPreview';
import WhatsAppConfig from './WhatsAppConfig';
import DeleteProjectModal from './DeleteProjectModal';

interface ProjectSettingsFormProps {
  projectId: string;
  initialData: {
    name: string;
    description?: string;
    subdomain?: string;
    seo_title?: string;
    seo_description?: string;
    whatsapp_number?: string;
    published?: boolean;
  };
}

export default function ProjectSettingsForm({
  projectId,
  initialData,
}: ProjectSettingsFormProps) {
  const [formData, setFormData] = useState({
    name: initialData.name || '',
    description: initialData.description || '',
    subdomain: initialData.subdomain || '',
    seo_title: initialData.seo_title || initialData.name || '',
    seo_description: initialData.seo_description || initialData.description || '',
    whatsapp_number: initialData.whatsapp_number || '',
    published: initialData.published || false,
  });

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [subdomainValid, setSubdomainValid] = useState(true);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Track changes
  useEffect(() => {
    const changed =
      formData.name !== (initialData.name || '') ||
      formData.description !== (initialData.description || '') ||
      formData.subdomain !== (initialData.subdomain || '') ||
      formData.seo_title !== (initialData.seo_title || initialData.name || '') ||
      formData.seo_description !== (initialData.seo_description || initialData.description || '') ||
      formData.whatsapp_number !== (initialData.whatsapp_number || '') ||
      formData.published !== (initialData.published || false);
    
    setHasChanges(changed);
  }, [formData, initialData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      setError('Project name is required');
      return;
    }

    if (formData.subdomain && !subdomainValid) {
      setError('Please fix subdomain errors before saving');
      return;
    }

    setSaving(true);
    setError(null);
    setSaved(false);

    try {
      await api.projects.update(projectId, {
        name: formData.name,
        description: formData.description || undefined,
        subdomain: formData.subdomain || undefined,
        seo_title: formData.seo_title || undefined,
        seo_description: formData.seo_description || undefined,
        whatsapp_number: formData.whatsapp_number || undefined,
        published: formData.published,
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

  return (
    <div className="space-y-8">
      <form onSubmit={handleSubmit} className="space-y-8">
        {/* General Settings */}
        <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg">
          <div className="px-4 py-6 sm:p-8">
            <div className="max-w-2xl space-y-6">
              <div>
                <h2 className="text-base font-semibold leading-7 text-gray-900">
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

              {/* Project Description */}
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  id="description"
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
                  maxLength={500}
                />
                <p className="mt-1 text-xs text-gray-500">
                  {formData.description.length}/500 characters
                </p>
              </div>

              {/* Visibility Toggle */}
              {/* <div className="flex items-center justify-between py-4 border-t border-gray-200">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Project Visibility</h3>
                  <p className="text-sm text-gray-500">
                    {formData.published ? 'Public - Anyone can view' : 'Private - Only you can view'}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, published: !formData.published })}
                  className={`${
                    formData.published ? 'bg-indigo-600' : 'bg-gray-200'
                  } relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2`}
                >
                  <span
                    className={`${
                      formData.published ? 'translate-x-5' : 'translate-x-0'
                    } pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out`}
                  />
                </button>
              </div> */}
            </div>
          </div>
        </div>

        {/* Subdomain Configuration */}
        {/* <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg">
          <div className="px-4 py-6 sm:p-8">
            <div className="max-w-2xl space-y-6">
              <div>
                <h2 className="text-base font-semibold leading-7 text-gray-900">
                  Subdomain Configuration
                </h2>
                <p className="mt-1 text-sm leading-6 text-gray-600">
                  Set your custom subdomain for easy access
                </p>
              </div>

              <SubdomainInput
                value={formData.subdomain}
                onChange={(value) => setFormData({ ...formData, subdomain: value })}
                onValidationChange={setSubdomainValid}
              />
            </div>
          </div>
        </div> */}

        {/* SEO Settings */}
        {/* <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg">
          <div className="px-4 py-6 sm:p-8">
            <div className="max-w-2xl space-y-6"> */}
              {/* <div>
                <h2 className="text-base font-semibold leading-7 text-gray-900">
                  SEO Settings
                </h2>
                <p className="mt-1 text-sm leading-6 text-gray-600">
                  Optimize your site for search engines
                </p>
              </div> */}

              {/* SEO Title */}
              {/* <div>
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
              </div> */}

              {/* SEO Description */}
              {/* <div>
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
                  placeholder={formData.description}
                />
              </div> */}

              {/* SEO Preview */}
              {/* <SEOPreview
                title={formData.seo_title}
                description={formData.seo_description}
                subdomain={formData.subdomain}
              /> */}
            {/* </div>
          </div>
        </div> */}

        {/* WhatsApp Integration */}
        {/* <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg">
          <div className="px-4 py-6 sm:p-8">
            <div className="max-w-2xl space-y-6">
              <div>
                <h2 className="text-base font-semibold leading-7 text-gray-900">
                  WhatsApp Business
                </h2>
                <p className="mt-1 text-sm leading-6 text-gray-600">
                  Enable direct WhatsApp communication with your visitors
                </p>
              </div>

              <WhatsAppConfig
                value={formData.whatsapp_number}
                onChange={(value) => setFormData({ ...formData, whatsapp_number: value })}
              />
            </div>
          </div>
        </div> */}

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

      {/* Danger Zone */}
      <div className="bg-white shadow-sm ring-1 ring-red-900/10 sm:rounded-lg border-red-200 border">
        <div className="px-4 py-6 sm:p-8">
          <div className="max-w-2xl">
            <h2 className="text-base font-semibold leading-7 text-red-900">Danger Zone</h2>
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

