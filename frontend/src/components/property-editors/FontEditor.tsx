'use client';

import { useState } from 'react';
import { Type, ChevronDown } from 'lucide-react';
import { TAILWIND_FONT_SIZES, TAILWIND_FONT_WEIGHTS } from '@/types/property-edit.types';

interface FontEditorProps {
  fontSize?: string;
  fontWeight?: string;
  fontFamily?: string;
  lineHeight?: string;
  textAlign?: string;
  textTransform?: string;
  onFontSizeChange?: (value: string) => void;
  onFontWeightChange?: (value: string) => void;
  onFontFamilyChange?: (value: string) => void;
  onLineHeightChange?: (value: string) => void;
  onTextAlignChange?: (value: string) => void;
  onTextTransformChange?: (value: string) => void;
}

const FONT_FAMILIES = [
  { value: 'font-sans', label: 'Sans Serif', family: 'sans-serif' },
  { value: 'font-serif', label: 'Serif', family: 'serif' },
  { value: 'font-mono', label: 'Monospace', family: 'monospace' },
];

const LINE_HEIGHTS = [
  { value: 'leading-none', label: 'None', height: '1' },
  { value: 'leading-tight', label: 'Tight', height: '1.25' },
  { value: 'leading-snug', label: 'Snug', height: '1.375' },
  { value: 'leading-normal', label: 'Normal', height: '1.5' },
  { value: 'leading-relaxed', label: 'Relaxed', height: '1.625' },
  { value: 'leading-loose', label: 'Loose', height: '2' },
];

const TEXT_TRANSFORMS = [
  { value: 'normal-case', label: 'None' },
  { value: 'uppercase', label: 'UPPERCASE' },
  { value: 'lowercase', label: 'lowercase' },
  { value: 'capitalize', label: 'Capitalize' },
];

export default function FontEditor({
  fontSize = 'text-base',
  fontWeight = 'font-normal',
  fontFamily = 'font-sans',
  lineHeight = 'leading-normal',
  textAlign = 'text-left',
  textTransform = 'normal-case',
  onFontSizeChange,
  onFontWeightChange,
  onFontFamilyChange,
  onLineHeightChange,
  onTextAlignChange,
  onTextTransformChange,
}: FontEditorProps) {
  const [showSizeDropdown, setShowSizeDropdown] = useState(false);
  const [showWeightDropdown, setShowWeightDropdown] = useState(false);

  return (
    <div className="space-y-4">
      {/* Info banner */}
      <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-2">
        <div className="text-xs text-blue-300">
          ✨ All changes apply instantly to the preview
        </div>
      </div>

      {/* Font Family */}
      {onFontFamilyChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Font Family</label>
          <div className="grid grid-cols-3 gap-2">
            {FONT_FAMILIES.map((font) => (
              <button
                key={font.value}
                onClick={() => onFontFamilyChange(font.value)}
                className={`px-3 py-2 text-xs rounded border transition-all ${
                  fontFamily === font.value
                    ? 'bg-blue-600 border-blue-500 text-white shadow-lg scale-105'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-blue-400 hover:bg-gray-750 hover:scale-105'
                }`}
                style={{ fontFamily: font.family }}
              >
                {font.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Font Size */}
      {onFontSizeChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Font Size</label>
          <div className="relative">
            <button
              onClick={() => setShowSizeDropdown(!showSizeDropdown)}
              className="w-full flex items-center justify-between px-3 py-2 bg-gray-800 border border-gray-700 rounded hover:border-gray-600 transition-colors"
            >
              <span className="text-sm text-gray-300">{fontSize}</span>
              <ChevronDown className="w-4 h-4 text-gray-500" />
            </button>
            
            {showSizeDropdown && (
              <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                <div className="p-2 space-y-1">
                  {TAILWIND_FONT_SIZES.map((size) => (
                    <button
                      key={size}
                      onClick={() => {
                        // Apply instantly but keep dropdown open for more changes
                        onFontSizeChange(size);
                        // Don't close dropdown
                      }}
                      className={`w-full px-3 py-2 text-left rounded transition-colors ${
                        fontSize === size ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'
                      }`}
                    >
                      <span className={`${size}`}>{size}</span>
                    </button>
                  ))}
                </div>
                <div className="p-2 border-t border-gray-700 flex justify-between items-center">
                  <span className="text-xs text-gray-400">Click to apply instantly</span>
                  <button
                    onClick={() => setShowSizeDropdown(false)}
                    className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                  >
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Font Weight */}
      {onFontWeightChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Font Weight</label>
          <div className="relative">
            <button
              onClick={() => setShowWeightDropdown(!showWeightDropdown)}
              className="w-full flex items-center justify-between px-3 py-2 bg-gray-800 border border-gray-700 rounded hover:border-gray-600 transition-colors"
            >
              <span className="text-sm text-gray-300">
                {TAILWIND_FONT_WEIGHTS.find(w => w.value === fontWeight)?.label || fontWeight}
              </span>
              <ChevronDown className="w-4 h-4 text-gray-500" />
            </button>
            
            {showWeightDropdown && (
              <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-lg">
                <div className="p-2 space-y-1">
                  {TAILWIND_FONT_WEIGHTS.map((weight) => (
                    <button
                      key={weight.value}
                      onClick={() => {
                        // Apply instantly but keep dropdown open for more changes
                        onFontWeightChange(weight.value);
                        // Don't close dropdown
                      }}
                      className={`w-full px-3 py-2 text-left rounded transition-colors ${
                        fontWeight === weight.value ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'
                      }`}
                    >
                      <span className={`${weight.value}`}>
                        {weight.label} ({weight.weight})
                      </span>
                    </button>
                  ))}
                </div>
                <div className="p-2 border-t border-gray-700 flex justify-between items-center">
                  <span className="text-xs text-gray-400">Click to apply instantly</span>
                  <button
                    onClick={() => setShowWeightDropdown(false)}
                    className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                  >
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Line Height */}
      {onLineHeightChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Line Height</label>
          <div className="grid grid-cols-3 gap-2">
            {LINE_HEIGHTS.map((lh) => (
              <button
                key={lh.value}
                onClick={() => onLineHeightChange(lh.value)}
                className={`px-3 py-2 text-xs rounded border transition-all ${
                  lineHeight === lh.value
                    ? 'bg-blue-600 border-blue-500 text-white shadow-lg scale-105'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-blue-400 hover:bg-gray-750 hover:scale-105'
                }`}
              >
                {lh.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Text Alignment */}
      {onTextAlignChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Text Alignment</label>
          <div className="grid grid-cols-4 gap-2">
            {['text-left', 'text-center', 'text-right', 'text-justify'].map((align) => {
              const labels = {
                'text-left': 'Left',
                'text-center': 'Center',
                'text-right': 'Right',
                'text-justify': 'Justify',
              };
              return (
                <button
                  key={align}
                  onClick={() => onTextAlignChange(align)}
                  className={`px-3 py-2 text-xs rounded border transition-all ${
                    textAlign === align
                      ? 'bg-blue-600 border-blue-500 text-white shadow-lg scale-105'
                      : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-blue-400 hover:bg-gray-750 hover:scale-105'
                  }`}
                >
                  {labels[align as keyof typeof labels]}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Text Transform */}
      {onTextTransformChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Text Transform</label>
          <div className="grid grid-cols-2 gap-2">
            {TEXT_TRANSFORMS.map((transform) => (
              <button
                key={transform.value}
                onClick={() => onTextTransformChange(transform.value)}
                className={`px-3 py-2 text-xs rounded border transition-all ${
                  textTransform === transform.value
                    ? 'bg-blue-600 border-blue-500 text-white shadow-lg scale-105'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-blue-400 hover:bg-gray-750 hover:scale-105'
                }`}
              >
                {transform.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

