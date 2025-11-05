'use client';

import { Link as LinkIcon, ExternalLink } from 'lucide-react';

interface LinkEditorProps {
  href?: string;
  target?: string;
  rel?: string;
  onHrefChange?: (value: string) => void;
  onTargetChange?: (value: string) => void;
  onRelChange?: (value: string) => void;
}

export default function LinkEditor({
  href = '',
  target = '_self',
  rel = '',
  onHrefChange,
  onTargetChange,
  onRelChange,
}: LinkEditorProps) {
  return (
    <div className="space-y-4">
      {/* URL Input */}
      {onHrefChange && (
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs font-medium text-gray-400">
            <LinkIcon className="w-3 h-3" />
            URL
          </label>
          <input
            type="text"
            value={href}
            onChange={(e) => onHrefChange(e.target.value)}
            placeholder="https://example.com"
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-300 focus:outline-none focus:border-blue-500"
          />
        </div>
      )}

      {/* Target */}
      {onTargetChange && (
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs font-medium text-gray-400">
            <ExternalLink className="w-3 h-3" />
            Open Link In
          </label>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => onTargetChange('_self')}
              className={`px-3 py-2 text-xs rounded border transition-colors ${
                target === '_self'
                  ? 'bg-blue-600 border-blue-500 text-white'
                  : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
              }`}
            >
              Same Tab
            </button>
            <button
              onClick={() => onTargetChange('_blank')}
              className={`px-3 py-2 text-xs rounded border transition-colors ${
                target === '_blank'
                  ? 'bg-blue-600 border-blue-500 text-white'
                  : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
              }`}
            >
              New Tab
            </button>
          </div>
        </div>
      )}

      {/* Rel Attributes */}
      {onRelChange && target === '_blank' && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Security</label>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-xs text-gray-300">
              <input
                type="checkbox"
                checked={rel.includes('noopener')}
                onChange={(e) => {
                  const newRel = e.target.checked
                    ? [...rel.split(' '), 'noopener'].filter(Boolean).join(' ')
                    : rel.replace('noopener', '').trim();
                  onRelChange(newRel);
                }}
                className="rounded border-gray-600"
              />
              noopener (recommended for security)
            </label>
            <label className="flex items-center gap-2 text-xs text-gray-300">
              <input
                type="checkbox"
                checked={rel.includes('noreferrer')}
                onChange={(e) => {
                  const newRel = e.target.checked
                    ? [...rel.split(' '), 'noreferrer'].filter(Boolean).join(' ')
                    : rel.replace('noreferrer', '').trim();
                  onRelChange(newRel);
                }}
                className="rounded border-gray-600"
              />
              noreferrer (hide referrer)
            </label>
          </div>
        </div>
      )}
    </div>
  );
}

