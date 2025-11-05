'use client';

import { useState } from 'react';
import { Box, Link as LinkIcon } from 'lucide-react';
import { TAILWIND_SPACING } from '@/types/property-edit.types';

interface SpacingEditorProps {
  paddingTop?: string;
  paddingRight?: string;
  paddingBottom?: string;
  paddingLeft?: string;
  marginTop?: string;
  marginRight?: string;
  marginBottom?: string;
  marginLeft?: string;
  gap?: string;
  onPaddingChange?: (side: 'top' | 'right' | 'bottom' | 'left' | 'all', value: string) => void;
  onMarginChange?: (side: 'top' | 'right' | 'bottom' | 'left' | 'all', value: string) => void;
  onGapChange?: (value: string) => void;
}

export default function SpacingEditor({
  paddingTop = '0',
  paddingRight = '0',
  paddingBottom = '0',
  paddingLeft = '0',
  marginTop = '0',
  marginRight = '0',
  marginBottom = '0',
  marginLeft = '0',
  gap = '0',
  onPaddingChange,
  onMarginChange,
  onGapChange,
}: SpacingEditorProps) {
  const [mode, setMode = useState<'padding' | 'margin' | 'gap'>('padding');
  const [uniformMode, setUniformMode] = useState(true);

  const renderSpacingInput = (
    label: string,
    value: string,
    onChange: (value: string) => void
  ) => (
    <div className="space-y-1">
      <label className="text-xs text-gray-400">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-2 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-gray-300 focus:outline-none focus:border-blue-500"
      >
        {TAILWIND_SPACING.map((spacing) => (
          <option key={spacing.value} value={spacing.value}>
            {spacing.label} ({spacing.px})
          </option>
        ))}
      </select>
    </div>
  );

  const renderBoxModel = () => (
    <div className="relative w-full aspect-square max-w-xs mx-auto">
      {/* Margin (outer) */}
      <div className="absolute inset-0 border-2 border-dashed border-yellow-500/50 rounded-lg flex items-center justify-center">
        <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs text-yellow-500">
          Margin
        </div>
        
        {/* Padding (inner) */}
        <div className="w-3/4 h-3/4 border-2 border-dashed border-blue-500/50 rounded-lg flex items-center justify-center">
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-8 text-xs text-blue-500">
            Padding
          </div>
          
          {/* Content */}
          <div className="w-1/2 h-1/2 bg-gray-700 rounded flex items-center justify-center">
            <Box className="w-6 h-6 text-gray-500" />
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      {/* Mode Selector */}
      <div className="grid grid-cols-3 gap-2">
        <button
          onClick={() => setMode('padding')}
          className={`px-3 py-2 text-xs rounded border transition-colors ${
            mode === 'padding'
              ? 'bg-blue-600 border-blue-500 text-white'
              : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
          }`}
        >
          Padding
        </button>
        <button
          onClick={() => setMode('margin')}
          className={`px-3 py-2 text-xs rounded border transition-colors ${
            mode === 'margin'
              ? 'bg-yellow-600 border-yellow-500 text-white'
              : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
          }`}
        >
          Margin
        </button>
        <button
          onClick={() => setMode('gap')}
          className={`px-3 py-2 text-xs rounded border transition-colors ${
            mode === 'gap'
              ? 'bg-green-600 border-green-500 text-white'
              : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
          }`}
        >
          Gap
        </button>
      </div>

      {/* Box Model Visualization */}
      {(mode === 'padding' || mode === 'margin') && renderBoxModel()}

      {/* Uniform Mode Toggle */}
      {(mode === 'padding' || mode === 'margin') && (
        <div className="flex items-center gap-2 p-2 bg-gray-800/50 rounded border border-gray-700">
          <input
            type="checkbox"
            id="uniformMode"
            checked={uniformMode}
            onChange={(e) => setUniformMode(e.target.checked)}
            className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="uniformMode" className="flex items-center gap-2 text-xs text-gray-300 cursor-pointer">
            <LinkIcon className="w-3 h-3" />
            Apply to all sides
          </label>
        </div>
      )}

      {/* Spacing Controls */}
      {mode === 'padding' && onPaddingChange && (
        <div className="space-y-3">
          {uniformMode ? (
            renderSpacingInput('All Sides', paddingTop, (value) =>
              onPaddingChange('all', value)
            )
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {renderSpacingInput('Top', paddingTop, (value) =>
                onPaddingChange('top', value)
              )}
              {renderSpacingInput('Right', paddingRight, (value) =>
                onPaddingChange('right', value)
              )}
              {renderSpacingInput('Bottom', paddingBottom, (value) =>
                onPaddingChange('bottom', value)
              )}
              {renderSpacingInput('Left', paddingLeft, (value) =>
                onPaddingChange('left', value)
              )}
            </div>
          )}
        </div>
      )}

      {mode === 'margin' && onMarginChange && (
        <div className="space-y-3">
          {uniformMode ? (
            renderSpacingInput('All Sides', marginTop, (value) =>
              onMarginChange('all', value)
            )
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {renderSpacingInput('Top', marginTop, (value) =>
                onMarginChange('top', value)
              )}
              {renderSpacingInput('Right', marginRight, (value) =>
                onMarginChange('right', value)
              )}
              {renderSpacingInput('Bottom', marginBottom, (value) =>
                onMarginChange('bottom', value)
              )}
              {renderSpacingInput('Left', marginLeft, (value) =>
                onMarginChange('left', value)
              )}
            </div>
          )}
        </div>
      )}

      {mode === 'gap' && onGapChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Gap (for Flex/Grid)</label>
          <select
            value={gap}
            onChange={(e) => onGapChange(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-300 focus:outline-none focus:border-blue-500"
          >
            {TAILWIND_SPACING.map((spacing) => (
              <option key={spacing.value} value={`gap-${spacing.value}`}>
                gap-{spacing.label} ({spacing.px})
              </option>
            ))}
          </select>
          <div className="text-xs text-gray-500">
            Gap applies spacing between flex/grid items
          </div>
        </div>
      )}

      {/* Quick Presets */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-gray-400">Quick Presets</label>
        <div className="flex flex-wrap gap-2">
          {['0', '2', '4', '6', '8', '12', '16'].map((preset) => (
            <button
              key={preset}
              onClick={() => {
                if (mode === 'padding' && onPaddingChange) {
                  onPaddingChange('all', preset);
                } else if (mode === 'margin' && onMarginChange) {
                  onMarginChange('all', preset);
                } else if (mode === 'gap' && onGapChange) {
                  onGapChange(`gap-${preset}`);
                }
              }}
              className="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded text-gray-300 transition-colors"
            >
              {preset === '0' ? 'None' : `${TAILWIND_SPACING.find(s => s.value === preset)?.px || preset}`}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

