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
      {/* Font Family */}
      {onFontFamilyChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Font Family</label>
          <div className="grid grid-cols-3 gap-2">
            {FONT_FAMILIES.map((font) => (
              <button
                key={font.value}
                onClick={() => onFontFamilyChange(font.value)}
                className={`px-3 py-2 text-xs rounded border transition-colors ${
                  fontFamily === font.value
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
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
                {TAILWIND_FONT_SIZES.map((size) => (
                  <button
                    key={size}
                    onClick={() => {
                      onFontSizeChange(size);
                      setShowSizeDropdown(false);
                    }}
                    className={`w-full px-3 py-2 text-left hover:bg-gray-700 transition-colors ${
                      fontSize === size ? 'bg-blue-600 text-white' : 'text-gray-300'
                    }`}
                  >
                    <span className={`${size}`}>{size}</span>
                  </button>
                ))}
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
                {TAILWIND_FONT_WEIGHTS.map((weight) => (
                  <button
                    key={weight.value}
                    onClick={() => {
                      onFontWeightChange(weight.value);
                      setShowWeightDropdown(false);
                    }}
                    className={`w-full px-3 py-2 text-left hover:bg-gray-700 transition-colors ${
                      fontWeight === weight.value ? 'bg-blue-600 text-white' : 'text-gray-300'
                    }`}
                  >
                    <span className={`${weight.value}`}>
                      {weight.label} ({weight.weight})
                    </span>
                  </button>
                ))}
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
                className={`px-3 py-2 text-xs rounded border transition-colors ${
                  lineHeight === lh.value
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
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
                  className={`px-3 py-2 text-xs rounded border transition-colors ${
                    textAlign === align
                      ? 'bg-blue-600 border-blue-500 text-white'
                      : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
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
                className={`px-3 py-2 text-xs rounded border transition-colors ${
                  textTransform === transform.value
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
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

