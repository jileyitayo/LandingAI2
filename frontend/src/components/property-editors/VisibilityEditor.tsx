'use client';

import { Eye, EyeOff, Monitor, Tablet, Smartphone } from 'lucide-react';

interface VisibilityEditorProps {
  isVisible?: boolean;
  hiddenOnMobile?: boolean;
  hiddenOnTablet?: boolean;
  hiddenOnDesktop?: boolean;
  overflow?: string;
  onVisibilityChange?: (visible: boolean) => void;
  onResponsiveVisibilityChange?: (device: 'mobile' | 'tablet' | 'desktop', hidden: boolean) => void;
  onOverflowChange?: (value: string) => void;
}

const OVERFLOW_OPTIONS = [
  { value: 'overflow-visible', label: 'Visible' },
  { value: 'overflow-hidden', label: 'Hidden' },
  { value: 'overflow-scroll', label: 'Scroll' },
  { value: 'overflow-auto', label: 'Auto' },
];

export default function VisibilityEditor({
  isVisible = true,
  hiddenOnMobile = false,
  hiddenOnTablet = false,
  hiddenOnDesktop = false,
  overflow = 'overflow-visible',
  onVisibilityChange,
  onResponsiveVisibilityChange,
  onOverflowChange,
}: VisibilityEditorProps) {
  return (
    <div className="space-y-4">
      {/* Main Visibility Toggle */}
      {onVisibilityChange && (
        <div className="flex items-center justify-between p-3 bg-gray-800 rounded border border-gray-700">
          <div className="flex items-center gap-2">
            {isVisible ? (
              <Eye className="w-4 h-4 text-green-400" />
            ) : (
              <EyeOff className="w-4 h-4 text-red-400" />
            )}
            <span className="text-sm text-gray-300">
              {isVisible ? 'Visible' : 'Hidden'}
            </span>
          </div>
          <button
            onClick={() => onVisibilityChange(!isVisible)}
            className={`px-4 py-2 text-xs rounded transition-colors ${
              isVisible
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-red-600 hover:bg-red-700 text-white'
            }`}
          >
            {isVisible ? 'Hide' : 'Show'}
          </button>
        </div>
      )}

      {/* Responsive Visibility */}
      {onResponsiveVisibilityChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Responsive Visibility</label>
          <div className="space-y-2">
            <label className="flex items-center justify-between p-2 bg-gray-800 rounded border border-gray-700 hover:border-gray-600 cursor-pointer">
              <div className="flex items-center gap-2">
                <Smartphone className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-300">Mobile</span>
              </div>
              <input
                type="checkbox"
                checked={!hiddenOnMobile}
                onChange={(e) => onResponsiveVisibilityChange('mobile', !e.target.checked)}
                className="rounded border-gray-600"
              />
            </label>

            <label className="flex items-center justify-between p-2 bg-gray-800 rounded border border-gray-700 hover:border-gray-600 cursor-pointer">
              <div className="flex items-center gap-2">
                <Tablet className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-300">Tablet</span>
              </div>
              <input
                type="checkbox"
                checked={!hiddenOnTablet}
                onChange={(e) => onResponsiveVisibilityChange('tablet', !e.target.checked)}
                className="rounded border-gray-600"
              />
            </label>

            <label className="flex items-center justify-between p-2 bg-gray-800 rounded border border-gray-700 hover:border-gray-600 cursor-pointer">
              <div className="flex items-center gap-2">
                <Monitor className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-300">Desktop</span>
              </div>
              <input
                type="checkbox"
                checked={!hiddenOnDesktop}
                onChange={(e) => onResponsiveVisibilityChange('desktop', !e.target.checked)}
                className="rounded border-gray-600"
              />
            </label>
          </div>
        </div>
      )}

      {/* Overflow */}
      {onOverflowChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Overflow</label>
          <div className="grid grid-cols-2 gap-2">
            {OVERFLOW_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => onOverflowChange(option.value)}
                className={`px-3 py-2 text-xs rounded border transition-colors ${
                  overflow === option.value
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

