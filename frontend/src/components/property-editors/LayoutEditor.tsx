'use client';

import { Layout, Layers } from 'lucide-react';

interface LayoutEditorProps {
  display?: string;
  position?: string;
  flexDirection?: string;
  justifyContent?: string;
  alignItems?: string;
  flexWrap?: string;
  zIndex?: string;
  onDisplayChange?: (value: string) => void;
  onPositionChange?: (value: string) => void;
  onFlexDirectionChange?: (value: string) => void;
  onJustifyContentChange?: (value: string) => void;
  onAlignItemsChange?: (value: string) => void;
  onFlexWrapChange?: (value: string) => void;
  onZIndexChange?: (value: string) => void;
}

const DISPLAY_TYPES = [
  { value: 'block', label: 'Block' },
  { value: 'inline-block', label: 'Inline Block' },
  { value: 'inline', label: 'Inline' },
  { value: 'flex', label: 'Flex' },
  { value: 'inline-flex', label: 'Inline Flex' },
  { value: 'grid', label: 'Grid' },
  { value: 'hidden', label: 'Hidden' },
];

const POSITION_TYPES = [
  { value: 'static', label: 'Static' },
  { value: 'relative', label: 'Relative' },
  { value: 'absolute', label: 'Absolute' },
  { value: 'fixed', label: 'Fixed' },
  { value: 'sticky', label: 'Sticky' },
];

const FLEX_DIRECTIONS = [
  { value: 'flex-row', label: 'Row →' },
  { value: 'flex-row-reverse', label: '← Row' },
  { value: 'flex-col', label: 'Column ↓' },
  { value: 'flex-col-reverse', label: '↑ Column' },
];

const JUSTIFY_CONTENT = [
  { value: 'justify-start', label: 'Start' },
  { value: 'justify-center', label: 'Center' },
  { value: 'justify-end', label: 'End' },
  { value: 'justify-between', label: 'Between' },
  { value: 'justify-around', label: 'Around' },
  { value: 'justify-evenly', label: 'Evenly' },
];

const ALIGN_ITEMS = [
  { value: 'items-start', label: 'Start' },
  { value: 'items-center', label: 'Center' },
  { value: 'items-end', label: 'End' },
  { value: 'items-stretch', label: 'Stretch' },
  { value: 'items-baseline', label: 'Baseline' },
];

export default function LayoutEditor({
  display = 'block',
  position = 'static',
  flexDirection = 'flex-row',
  justifyContent = 'justify-start',
  alignItems = 'items-start',
  flexWrap = 'flex-nowrap',
  zIndex = '0',
  onDisplayChange,
  onPositionChange,
  onFlexDirectionChange,
  onJustifyContentChange,
  onAlignItemsChange,
  onFlexWrapChange,
  onZIndexChange,
}: LayoutEditorProps) {
  const isFlex = display === 'flex' || display === 'inline-flex';

  return (
    <div className="space-y-4">
      {/* Display Type */}
      {onDisplayChange && (
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs font-medium text-gray-400">
            <Layout className="w-3 h-3" />
            Display
          </label>
          <div className="grid grid-cols-2 gap-2">
            {DISPLAY_TYPES.map((type) => (
              <button
                key={type.value}
                onClick={() => onDisplayChange(type.value)}
                className={`px-3 py-2 text-xs rounded border transition-colors ${
                  display === type.value
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
                }`}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Position */}
      {onPositionChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Position</label>
          <div className="grid grid-cols-3 gap-2">
            {POSITION_TYPES.map((type) => (
              <button
                key={type.value}
                onClick={() => onPositionChange(type.value)}
                className={`px-3 py-2 text-xs rounded border transition-colors ${
                  position === type.value
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
                }`}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Flex Container Options */}
      {isFlex && (
        <div className="space-y-4 p-3 bg-blue-900/10 border border-blue-700/30 rounded-lg">
          <div className="text-xs font-medium text-blue-400">Flexbox Controls</div>

          {/* Flex Direction */}
          {onFlexDirectionChange && (
            <div className="space-y-2">
              <label className="text-xs text-gray-400">Direction</label>
              <div className="grid grid-cols-2 gap-2">
                {FLEX_DIRECTIONS.map((dir) => (
                  <button
                    key={dir.value}
                    onClick={() => onFlexDirectionChange(dir.value)}
                    className={`px-3 py-2 text-xs rounded border transition-colors ${
                      flexDirection === dir.value
                        ? 'bg-blue-600 border-blue-500 text-white'
                        : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
                    }`}
                  >
                    {dir.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Justify Content */}
          {onJustifyContentChange && (
            <div className="space-y-2">
              <label className="text-xs text-gray-400">Justify (Main Axis)</label>
              <div className="grid grid-cols-3 gap-2">
                {JUSTIFY_CONTENT.map((justify) => (
                  <button
                    key={justify.value}
                    onClick={() => onJustifyContentChange(justify.value)}
                    className={`px-2 py-2 text-xs rounded border transition-colors ${
                      justifyContent === justify.value
                        ? 'bg-blue-600 border-blue-500 text-white'
                        : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
                    }`}
                  >
                    {justify.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Align Items */}
          {onAlignItemsChange && (
            <div className="space-y-2">
              <label className="text-xs text-gray-400">Align (Cross Axis)</label>
              <div className="grid grid-cols-3 gap-2">
                {ALIGN_ITEMS.map((align) => (
                  <button
                    key={align.value}
                    onClick={() => onAlignItemsChange(align.value)}
                    className={`px-2 py-2 text-xs rounded border transition-colors ${
                      alignItems === align.value
                        ? 'bg-blue-600 border-blue-500 text-white'
                        : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
                    }`}
                  >
                    {align.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Flex Wrap */}
          {onFlexWrapChange && (
            <div className="space-y-2">
              <label className="text-xs text-gray-400">Wrap</label>
              <div className="grid grid-cols-3 gap-2">
                {['flex-nowrap', 'flex-wrap', 'flex-wrap-reverse'].map((wrap) => (
                  <button
                    key={wrap}
                    onClick={() => onFlexWrapChange(wrap)}
                    className={`px-3 py-2 text-xs rounded border transition-colors ${
                      flexWrap === wrap
                        ? 'bg-blue-600 border-blue-500 text-white'
                        : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
                    }`}
                  >
                    {wrap.replace('flex-', '')}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Z-Index */}
      {onZIndexChange && (
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs font-medium text-gray-400">
            <Layers className="w-3 h-3" />
            Z-Index (Stacking Order)
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              value={zIndex}
              onChange={(e) => onZIndexChange(e.target.value)}
              className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-300 focus:outline-none focus:border-blue-500"
              placeholder="0"
            />
            <div className="flex gap-1">
              {['0', '10', '20', '50'].map((preset) => (
                <button
                  key={preset}
                  onClick={() => onZIndexChange(preset)}
                  className="px-3 py-2 text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded text-gray-300 transition-colors"
                >
                  {preset}
                </button>
              ))}
            </div>
          </div>
          <div className="text-xs text-gray-500">
            Higher values appear on top
          </div>
        </div>
      )}
    </div>
  );
}

