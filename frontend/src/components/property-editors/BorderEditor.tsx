'use client';

import { useState } from 'react';
import { Square } from 'lucide-react';
import { TAILWIND_BORDER_RADIUS } from '@/types/property-edit.types';

interface BorderEditorProps {
  borderWidth?: string;
  borderStyle?: string;
  borderColor?: string;
  borderRadius?: string;
  onBorderWidthChange?: (value: string) => void;
  onBorderStyleChange?: (value: string) => void;
  onBorderColorChange?: (value: string) => void;
  onBorderRadiusChange?: (value: string) => void;
}

const BORDER_WIDTHS = [
  { value: 'border-0', label: 'None', px: '0px' },
  { value: 'border', label: 'Default', px: '1px' },
  { value: 'border-2', label: '2px', px: '2px' },
  { value: 'border-4', label: '4px', px: '4px' },
  { value: 'border-8', label: '8px', px: '8px' },
];

const BORDER_STYLES = [
  { value: 'border-solid', label: 'Solid' },
  { value: 'border-dashed', label: 'Dashed' },
  { value: 'border-dotted', label: 'Dotted' },
  { value: 'border-double', label: 'Double' },
  { value: 'border-none', label: 'None' },
];

export default function BorderEditor({
  borderWidth = 'border',
  borderStyle = 'border-solid',
  borderColor = 'border-gray-300',
  borderRadius = 'rounded',
  onBorderWidthChange,
  onBorderStyleChange,
  onBorderColorChange,
  onBorderRadiusChange,
}: BorderEditorProps) {
  const [showColorPicker, setShowColorPicker] = useState(false);

  return (
    <div className="space-y-4">
      {/* Border Preview */}
      <div className="flex items-center justify-center p-6 bg-gray-800/50 rounded">
        <div
          className={`w-32 h-32 bg-gray-700 ${borderWidth} ${borderStyle} ${borderColor} ${borderRadius} flex items-center justify-center`}
        >
          <Square className="w-8 h-8 text-gray-500" />
        </div>
      </div>

      {/* Border Width */}
      {onBorderWidthChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Border Width</label>
          <div className="grid grid-cols-5 gap-2">
            {BORDER_WIDTHS.map((width) => (
              <button
                key={width.value}
                onClick={() => onBorderWidthChange(width.value)}
                className={`px-2 py-2 text-xs rounded border transition-colors ${
                  borderWidth === width.value
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
                }`}
              >
                <div>{width.label}</div>
                <div className="text-xs text-gray-500">{width.px}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Border Style */}
      {onBorderStyleChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Border Style</label>
          <div className="grid grid-cols-3 gap-2">
            {BORDER_STYLES.map((style) => (
              <button
                key={style.value}
                onClick={() => onBorderStyleChange(style.value)}
                className={`px-3 py-2 text-xs rounded border transition-colors ${
                  borderStyle === style.value
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
                }`}
              >
                {style.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Border Color */}
      {onBorderColorChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Border Color</label>
          <button
            onClick={() => setShowColorPicker(!showColorPicker)}
            className="w-full flex items-center gap-3 p-3 bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-gray-600 rounded transition-colors"
          >
            <div className={`w-10 h-10 rounded border-4 ${borderColor}`} />
            <div className="flex-1 text-left">
              <div className="text-sm text-gray-300 font-mono">{borderColor}</div>
              <div className="text-xs text-gray-500">Click to change</div>
            </div>
          </button>
          {showColorPicker && (
            <div className="text-xs text-gray-500 p-2 bg-gray-800/50 rounded border border-gray-700">
              Color picker will appear here (use ColorEditor component)
            </div>
          )}
        </div>
      )}

      {/* Border Radius */}
      {onBorderRadiusChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Border Radius</label>
          <div className="grid grid-cols-3 gap-2">
            {TAILWIND_BORDER_RADIUS.map((radius) => (
              <button
                key={radius.value}
                onClick={() => onBorderRadiusChange(radius.value)}
                className={`px-2 py-2 text-xs border transition-colors ${
                  borderRadius === radius.value
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
                } ${radius.value}`}
              >
                <div>{radius.label}</div>
                <div className="text-xs text-gray-500">{radius.px}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Individual Corner Radius (Advanced) */}
      <details className="text-xs text-gray-400">
        <summary className="cursor-pointer hover:text-gray-300">
          Advanced: Individual Corners
        </summary>
        <div className="mt-2 p-2 bg-gray-800/50 rounded border border-gray-700">
          Individual corner controls will be added here
        </div>
      </details>
    </div>
  );
}

