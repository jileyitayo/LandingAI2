'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { MessageSquare, Star, Sparkles, Bug, Lightbulb, Palette, X } from 'lucide-react';

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId?: string;
}

type ActionType = 'create_project' | 'edit_project' | 'generate_website' | 'edit_component' |
  'edit_properties' | 'publish_deploy' | 'download_project' | 'manage_settings' |
  'upload_avatar' | 'view_analytics' | 'duplicate_project' | 'delete_project' |
  'code_editing' | 'preview_project' | 'other';

type CategoryType = 'general' | 'bug' | 'feature' | 'ui/ux' | 'other';

export default function FeedbackModal({
  isOpen,
  onClose,
  projectId,
}: FeedbackModalProps) {
  const [category, setCategory] = useState<CategoryType>('general');
  const [action, setAction] = useState<ActionType | ''>('');
  const [rating, setRating] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!message.trim()) {
      setError('Please enter your feedback');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const data: any = {
        message: message.trim(),
        category,
      };

      if (rating) {
        data.rating = rating;
      }

      if (action) {
        data.action = action;
      }

      if (projectId) {
        data.project_id = projectId;
      }

      await api.feedback.submit(data);
      setSuccess(true);

      // Reset form after 2 seconds and close modal
      setTimeout(() => {
        setMessage('');
        setRating(null);
        setAction('');
        setCategory('general');
        setSuccess(false);
        onClose();
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Failed to submit feedback');
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!submitting) {
      setMessage('');
      setRating(null);
      setAction('');
      setCategory('general');
      setError(null);
      setSuccess(false);
      onClose();
    }
  };

  // Category options with icons and colors
  const categoryOptions = [
    {
      value: 'general',
      label: 'General Feedback',
      icon: MessageSquare,
      description: 'Share your thoughts',
      color: 'blue'
    },
    {
      value: 'bug',
      label: 'Report a Bug',
      icon: Bug,
      description: 'Something not working?',
      color: 'red'
    },
    {
      value: 'feature',
      label: 'Feature Request',
      icon: Lightbulb,
      description: 'Suggest new ideas',
      color: 'yellow'
    },
    {
      value: 'ui/ux',
      label: 'UI/UX Improvement',
      icon: Palette,
      description: 'Design suggestions',
      color: 'purple'
    },
    {
      value: 'other',
      label: 'Other',
      icon: Sparkles,
      description: 'Something else',
      color: 'gray'
    },
  ];

  // Action options grouped by category
  const actionOptions = [
    { value: '', label: 'None selected', group: '' },
    { value: 'create_project', label: 'Create Project', group: 'Project' },
    { value: 'edit_project', label: 'Edit Project', group: 'Project' },
    { value: 'duplicate_project', label: 'Duplicate Project', group: 'Project' },
    { value: 'delete_project', label: 'Delete Project', group: 'Project' },
    { value: 'generate_website', label: 'Generate Website', group: 'Content' },
    { value: 'edit_component', label: 'Edit Component', group: 'Editing' },
    { value: 'edit_properties', label: 'Edit Properties', group: 'Editing' },
    { value: 'code_editing', label: 'Code Editing', group: 'Editing' },
    { value: 'preview_project', label: 'Preview Project', group: 'Preview' },
    { value: 'publish_deploy', label: 'Publish/Deploy', group: 'Deploy' },
    { value: 'download_project', label: 'Download Project', group: 'Export' },
    { value: 'manage_settings', label: 'Manage Settings', group: 'Settings' },
    { value: 'upload_avatar', label: 'Upload Avatar', group: 'Profile' },
    { value: 'view_analytics', label: 'View Analytics', group: 'Analytics' },
    { value: 'other', label: 'Other Action', group: 'Other' },
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        {/* Backdrop with blur effect */}
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
          onClick={handleClose}
        />

        {/* Modal */}
        <div className="relative transform overflow-hidden rounded-2xl bg-white shadow-2xl transition-all w-full max-w-2xl">
          {/* Close button */}
          <button
            onClick={handleClose}
            disabled={submitting}
            className="absolute right-4 top-4 z-10 rounded-full p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>

          <form onSubmit={handleSubmit}>
            {success ? (
              // Success state
              <div className="p-12 text-center">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-green-400 to-green-600 mb-6">
                  <svg
                    className="h-10 w-10 text-white"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  Thank You!
                </h3>
                <p className="text-gray-600">
                  Your feedback has been submitted successfully. We appreciate your input!
                </p>
              </div>
            ) : (
              <>
                {/* Header */}
                <div className="bg-gradient-to-r from-blue-500 to-purple-600 px-8 py-6 text-white">
                  <h2 className="text-2xl font-bold mb-2">We'd Love Your Feedback</h2>
                  <p className="text-blue-100">Help us improve by sharing your thoughts</p>
                </div>

                {/* Content */}
                <div className="p-8 space-y-6">
                  {/* Category Selection - Card Style */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-3">
                      What would you like to share? *
                    </label>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {categoryOptions.map((option) => {
                        const Icon = option.icon;
                        const isSelected = category === option.value;
                        const colorClasses = {
                          blue: isSelected ? 'bg-blue-50 border-blue-500 ring-2 ring-blue-500' : 'border-gray-200 hover:border-blue-300',
                          red: isSelected ? 'bg-red-50 border-red-500 ring-2 ring-red-500' : 'border-gray-200 hover:border-red-300',
                          yellow: isSelected ? 'bg-yellow-50 border-yellow-500 ring-2 ring-yellow-500' : 'border-gray-200 hover:border-yellow-300',
                          purple: isSelected ? 'bg-purple-50 border-purple-500 ring-2 ring-purple-500' : 'border-gray-200 hover:border-purple-300',
                          gray: isSelected ? 'bg-gray-50 border-gray-500 ring-2 ring-gray-500' : 'border-gray-200 hover:border-gray-300',
                        };

                        return (
                          <button
                            key={option.value}
                            type="button"
                            onClick={() => setCategory(option.value as CategoryType)}
                            disabled={submitting}
                            className={`relative flex flex-col items-center p-4 rounded-xl border-2 transition-all cursor-pointer disabled:opacity-50 ${colorClasses[option.color as keyof typeof colorClasses]}`}
                          >
                            <Icon className={`w-6 h-6 mb-2 ${isSelected ? `text-${option.color}-600` : 'text-gray-400'}`} />
                            <span className={`text-sm font-medium ${isSelected ? 'text-gray-900' : 'text-gray-700'}`}>
                              {option.label}
                            </span>
                            <span className="text-xs text-gray-500 mt-1">
                              {option.description}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Action Selection - Dropdown */}
                  <div>
                    <label
                      htmlFor="action"
                      className="block text-sm font-semibold text-gray-900 mb-2"
                    >
                      Related Action <span className="text-gray-500 font-normal">(Optional)</span>
                    </label>
                    <select
                      id="action"
                      value={action}
                      onChange={(e) => setAction(e.target.value as ActionType | '')}
                      className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 sm:text-sm px-4 py-3 border transition-all"
                      disabled={submitting}
                    >
                      {actionOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.group && option.value !== '' ? `${option.group} → ${option.label}` : option.label}
                        </option>
                      ))}
                    </select>
                    <p className="mt-1.5 text-xs text-gray-500">
                      What were you doing when you encountered this?
                    </p>
                  </div>

                  {/* Rating - Improved Stars */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-3">
                      Rate Your Experience <span className="text-gray-500 font-normal">(Optional)</span>
                    </label>
                    <div className="flex items-center space-x-3">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          onClick={() => setRating(star === rating ? null : star)}
                          disabled={submitting}
                          className="group relative focus:outline-none disabled:opacity-50 transition-transform hover:scale-110"
                        >
                          <Star
                            className={`w-10 h-10 transition-all ${
                              rating && star <= rating
                                ? 'text-yellow-400 fill-yellow-400 drop-shadow-sm'
                                : 'text-gray-300 group-hover:text-yellow-200'
                            }`}
                          />
                        </button>
                      ))}
                      {rating && (
                        <span className="ml-3 text-sm font-medium text-gray-700">
                          {rating === 5 ? 'Excellent!' : rating === 4 ? 'Good' : rating === 3 ? 'Okay' : rating === 2 ? 'Poor' : 'Very Poor'}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Message - Enhanced Textarea */}
                  <div>
                    <label
                      htmlFor="message"
                      className="block text-sm font-semibold text-gray-900 mb-2"
                    >
                      Your Feedback *
                    </label>
                    <textarea
                      id="message"
                      rows={5}
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder="Tell us what you think... Be as detailed as you'd like!"
                      className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 sm:text-sm px-4 py-3 border transition-all resize-none"
                      disabled={submitting}
                      required
                    />
                    <div className="mt-1.5 flex items-center justify-between">
                      <p className="text-xs text-gray-500">
                        Share your experience, suggestions, or issues
                      </p>
                      <span className="text-xs text-gray-400">
                        {message.length}/2000
                      </span>
                    </div>
                  </div>

                  {/* Error Message */}
                  {error && (
                    <div className="rounded-lg bg-red-50 border border-red-200 p-4 flex items-start space-x-3">
                      <svg className="w-5 h-5 text-red-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                      <p className="text-sm text-red-700 font-medium">{error}</p>
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="bg-gray-50 px-8 py-4 flex items-center justify-between border-t border-gray-200">
                  <p className="text-xs text-gray-500">
                    <span className="text-red-500">*</span> Required fields
                  </p>
                  <div className="flex items-center space-x-3">
                    <button
                      type="button"
                      onClick={handleClose}
                      disabled={submitting}
                      className="px-5 py-2.5 text-sm font-semibold text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={submitting || !message.trim()}
                      className="px-6 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
                    >
                      {submitting ? (
                        <span className="flex items-center space-x-2">
                          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          <span>Submitting...</span>
                        </span>
                      ) : (
                        'Submit Feedback'
                      )}
                    </button>
                  </div>
                </div>
              </>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
