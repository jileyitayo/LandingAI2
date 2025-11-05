'use client';

import { Maximize2 } from 'lucide-react';

interface SizingEditorProps {
  width?: string;
  height?: string;
  minWidth?: string;
  minHeight?: string;
  maxWidth?: string;
  maxHeight?: string;
  onWidthChange?: (value: string) => void;
  onHeightChange?: (value: string) => void;
  onMinWidthChange?: (value: string) => void;
  onMinHeightChange?: (value: string) => void;
  onMaxWidthChange?: (value: string) => void;
  onMaxHeightChange?: (value: string) => void;
}

const SIZE_PRESETS = [
  { value: 'auto', label: 'Auto' },
  { value: 'full', label: 'Full (100%)' },
  { value: 'screen', label: 'Screen (100vw/vh)' },
  { value: 'fit', label: 'Fit Content' },
  { value: 'min', label: 'Min Content' },
  { value: 'max', label: 'Max Content' },
];

export default function SizingEditor({
  width = 'auto',
  height = 'auto',
  minWidth,
  minHeight,
  maxWidth,
  maxHeight,
  onWidthChange,
  onHeightChange,
  onMinWidthChange,
  onMinHeightChange,
  onMaxWidthChange,
  onMaxHeightChange,
}: SizingEditorProps) {
  const renderSizeInput = (
    label: string,
    value: string | undefined,
    onChange?: (value: string) => void,
    showPresets = true
  ) => {
    if (!onChange) return null;

    return (
      <div className="space-y-2">
        <label className="text-xs font-medium text-gray-400">{label}</label>
        
        {showPresets && (
          <div className="grid grid-cols-3 gap-2 mb-2">
            {SIZE_PRESETS.map((preset) => (
              <button
                key={preset.value}
                onClick={() => onChange(preset.value)}
                className={`px-2 py-1.5 text-xs rounded border transition-colors ${
                  value === preset.value
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
        )}

        <div className="flex gap-2">
          <input
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder="e.g., 100px, 50%, 20rem"
            className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-300 focus:outline-none focus:border-blue-500"
          />
          <select
            onChange={(e) => {
              const unit = e.target.value;
              const numValue = value?.replace(/[^0-9]/g, '') || '100';
              onChange(`${numValue}${unit}`);
            }}
            className="px-2 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-300 focus:outline-none focus:border-blue-500"
          >
            <option value="px">px</option>
            <option value="%">%</option>
            <option value="rem">rem</option>
            <option value="em">em</option>
            <option value="vw">vw</option>
            <option value="vh">vh</option>
          </select>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Size Preview */}
      <div className="flex items-center justify-center p-6 bg-gray-800/50 rounded">
        <div className="text-center text-gray-400">
          <Maximize2 className="w-8 h-8 mx-auto mb-2" />
          <div className="text-xs">
            {width} × {height}
          </div>
        </div>
      </div>

      {/* Width */}
      {renderSizeInput('Width', width, onWidthChange)}

      {/* Height */}
      {renderSizeInput('Height', height, onHeightChange)}

      {/* Constraints */}
      <details className="text-xs text-gray-400">
        <summary className="cursor-pointer hover:text-gray-300 font-medium">
          Constraints (Min/Max)
        </summary>
        <div className="mt-3 space-y-4">
          {renderSizeInput('Min Width', minWidth, onMinWidthChange, false)}
          {renderSizeInput('Min Height', minHeight, onMinHeightChange, false)}
          {renderSizeInput('Max Width', maxWidth, onMaxWidthChange, false)}
          {renderSizeInput('Max Height', maxHeight, onMaxHeightChange, false)}
        </div>
      </details>

      {/* Responsive Hints */}
      <div className="text-xs text-gray-500 bg-gray-800/50 p-3 rounded border border-gray-700">
        <div className="font-medium text-gray-400 mb-1">💡 Responsive Tips</div>
        <ul className="space-y-1 list-disc list-inside">
          <li>Use % for responsive widths</li>
          <li>Use vw/vh for viewport-based sizing</li>
          <li>Use rem/em for scalable typography</li>
          <li>Use px for fixed dimensions</li>
        </ul>
      </div>
    </div>
  );
}

