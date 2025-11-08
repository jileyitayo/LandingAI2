'use client';

import { useState, useRef, useMemo } from 'react';
import { Palette, Droplet, Check, ChevronDown, ChevronUp } from 'lucide-react';
import { TAILWIND_COLORS, TAILWIND_COLOR_SHADES } from '@/types/property-edit.types';

const TAILWIND_COLOR_VALUES: Record<string, Record<string, string>> = {
  slate: {
    '50': '#f8fafc', '100': '#f1f5f9', '200': '#e2e8f0', '300': '#cbd5e1',
    '400': '#94a3b8', '500': '#64748b', '600': '#475569', '700': '#334155',
    '800': '#1e293b', '900': '#0f172a', '950': '#020617',
  },
  gray: {
    '50': '#f9fafb', '100': '#f3f4f6', '200': '#e5e7eb', '300': '#d1d5db',
    '400': '#9ca3af', '500': '#6b7280', '600': '#4b5563', '700': '#374151',
    '800': '#1f2937', '900': '#111827', '950': '#030712',
  },
  zinc: {
    '50': '#fafafa', '100': '#f4f4f5', '200': '#e4e4e7', '300': '#d4d4d8',
    '400': '#a1a1aa', '500': '#71717a', '600': '#52525b', '700': '#3f3f46',
    '800': '#27272a', '900': '#18181b', '950': '#09090b',
  },
  neutral: {
    '50': '#fafafa', '100': '#f5f5f5', '200': '#e5e5e5', '300': '#d4d4d4',
    '400': '#a3a3a3', '500': '#737373', '600': '#525252', '700': '#404040',
    '800': '#262626', '900': '#171717', '950': '#0a0a0a',
  },
  stone: {
    '50': '#fafaf9', '100': '#f5f5f4', '200': '#e7e5e4', '300': '#d6d3d1',
    '400': '#a8a29e', '500': '#78716c', '600': '#57534e', '700': '#44403c',
    '800': '#292524', '900': '#1c1917', '950': '#0c0a09',
  },
  red: {
    '50': '#fef2f2', '100': '#fee2e2', '200': '#fecaca', '300': '#fca5a5',
    '400': '#f87171', '500': '#ef4444', '600': '#dc2626', '700': '#b91c1c',
    '800': '#991b1b', '900': '#7f1d1d', '950': '#450a0a',
  },
  orange: {
    '50': '#fff7ed', '100': '#ffedd5', '200': '#fed7aa', '300': '#fdba74',
    '400': '#fb923c', '500': '#f97316', '600': '#ea580c', '700': '#c2410c',
    '800': '#9a3412', '900': '#7c2d12', '950': '#431407',
  },
  amber: {
    '50': '#fffbeb', '100': '#fef3c7', '200': '#fde68a', '300': '#fcd34d',
    '400': '#fbbf24', '500': '#f59e0b', '600': '#d97706', '700': '#b45309',
    '800': '#92400e', '900': '#78350f', '950': '#451a03',
  },
  yellow: {
    '50': '#fefce8', '100': '#fef9c3', '200': '#fef08a', '300': '#fde047',
    '400': '#facc15', '500': '#eab308', '600': '#ca8a04', '700': '#a16207',
    '800': '#854d0e', '900': '#713f12', '950': '#422006',
  },
  lime: {
    '50': '#f7fee7', '100': '#ecfccb', '200': '#d9f99d', '300': '#bef264',
    '400': '#a3e635', '500': '#84cc16', '600': '#65a30d', '700': '#4d7c0f',
    '800': '#365314', '900': '#1a2e05', '950': '#0f1a03',
  },
  green: {
    '50': '#f0fdf4', '100': '#dcfce7', '200': '#bbf7d0', '300': '#86efac',
    '400': '#4ade80', '500': '#22c55e', '600': '#16a34a', '700': '#15803d',
    '800': '#166534', '900': '#14532d', '950': '#052e16',
  },
  emerald: {
    '50': '#ecfdf5', '100': '#d1fae5', '200': '#a7f3d0', '300': '#6ee7b7',
    '400': '#34d399', '500': '#10b981', '600': '#059669', '700': '#047857',
    '800': '#065f46', '900': '#064e3b', '950': '#022c22',
  },
  teal: {
    '50': '#f0fdfa', '100': '#ccfbf1', '200': '#99f6e4', '300': '#5eead4',
    '400': '#2dd4bf', '500': '#14b8a6', '600': '#0d9488', '700': '#0f766e',
    '800': '#115e59', '900': '#134e4a', '950': '#042f2e',
  },
  cyan: {
    '50': '#ecfeff', '100': '#cffafe', '200': '#a5f3fc', '300': '#67e8f9',
    '400': '#22d3ee', '500': '#06b6d4', '600': '#0891b2', '700': '#0e7490',
    '800': '#155e75', '900': '#164e63', '950': '#083344',
  },
  sky: {
    '50': '#f0f9ff', '100': '#e0f2fe', '200': '#bae6fd', '300': '#7dd3fc',
    '400': '#38bdf8', '500': '#0ea5e9', '600': '#0284c7', '700': '#0369a1',
    '800': '#075985', '900': '#0c4a6e', '950': '#082f49',
  },
  blue: {
    '50': '#eff6ff', '100': '#dbeafe', '200': '#bfdbfe', '300': '#93c5fd',
    '400': '#60a5fa', '500': '#3b82f6', '600': '#2563eb', '700': '#1d4ed8',
    '800': '#1e40af', '900': '#1e3a8a', '950': '#172554',
  },
  indigo: {
    '50': '#eef2ff', '100': '#e0e7ff', '200': '#c7d2fe', '300': '#a5b4fc',
    '400': '#818cf8', '500': '#6366f1', '600': '#4f46e5', '700': '#4338ca',
    '800': '#3730a3', '900': '#312e81', '950': '#1e1b4b',
  },
  violet: {
    '50': '#f5f3ff', '100': '#ede9fe', '200': '#ddd6fe', '300': '#c4b5fd',
    '400': '#a78bfa', '500': '#8b5cf6', '600': '#7c3aed', '700': '#6d28d9',
    '800': '#5b21b6', '900': '#4c1d95', '950': '#2e1065',
  },
  purple: {
    '50': '#faf5ff', '100': '#f3e8ff', '200': '#e9d5ff', '300': '#d8b4fe',
    '400': '#c084fc', '500': '#a855f7', '600': '#9333ea', '700': '#7e22ce',
    '800': '#6b21a8', '900': '#581c87', '950': '#3b0764',
  },
  fuchsia: {
    '50': '#fdf4ff', '100': '#fae8ff', '200': '#f5d0fe', '300': '#f0abfc',
    '400': '#e879f9', '500': '#d946ef', '600': '#c026d3', '700': '#a21caf',
    '800': '#86198f', '900': '#701a75', '950': '#4a044e',
  },
  pink: {
    '50': '#fdf2f8', '100': '#fce7f3', '200': '#fbcfe8', '300': '#f9a8d4',
    '400': '#f472b6', '500': '#ec4899', '600': '#db2777', '700': '#be185d',
    '800': '#9f1239', '900': '#831843', '950': '#500724',
  },
  rose: {
    '50': '#fff1f2', '100': '#ffe4e6', '200': '#fecdd3', '300': '#fda4af',
    '400': '#fb7185', '500': '#f43f5e', '600': '#e11d48', '700': '#be123c',
    '800': '#9f1239', '900': '#881337', '950': '#4c0519',
  },
};

// Color categories for better organization
const COLOR_CATEGORIES = {
  neutrals: ['slate', 'gray', 'zinc', 'neutral', 'stone'],
  warm: ['red', 'orange', 'amber', 'yellow'],
  fresh: ['lime', 'green', 'emerald', 'teal'],
  cool: ['cyan', 'sky', 'blue', 'indigo'],
  vibrant: ['violet', 'purple', 'fuchsia', 'pink', 'rose'],
};

// Popular color combinations for quick selection
const POPULAR_COLORS = [
  { color: 'blue', shade: '600', label: 'Primary Blue' },
  { color: 'gray', shade: '900', label: 'Dark Gray' },
  { color: 'slate', shade: '700', label: 'Slate' },
  { color: 'red', shade: '600', label: 'Alert Red' },
  { color: 'green', shade: '600', label: 'Success Green' },
  { color: 'amber', shade: '500', label: 'Warning Amber' },
  { color: 'purple', shade: '600', label: 'Royal Purple' },
  { color: 'teal', shade: '600', label: 'Teal' },
];

interface ColorEditorProps {
  label: string;
  value: string; // Tailwind class like "text-blue-500" or "bg-red-600"
  onChange: (value: string) => void;
  type: 'text' | 'background' | 'border';
  recentColors?: string[];
  onAddToRecent?: (color: string) => void;
  autoSave?: boolean;
}

export default function ColorEditor({
  label,
  value,
  onChange,
  type,
  recentColors = [],
  onAddToRecent,
  autoSave = true,
}: ColorEditorProps) {
  const [showPicker, setShowPicker] = useState(false);
  const [selectedColor, setSelectedColor] = useState<string | null>(null);
  const [selectedShade, setSelectedShade] = useState<string>('500');
  const [customHex, setCustomHex] = useState('');
  const [expandedCategory, setExpandedCategory] = useState<string | null>('neutrals');
  const colorInputRef = useRef<HTMLInputElement>(null);

  // Extract color info from Tailwind class
  const extractColorInfo = (tailwindClass: string) => {
    const prefix = type === 'text' ? 'text-' : type === 'background' ? 'bg-' : 'border-';
    const colorPart = tailwindClass.replace(prefix, '');
    
    // Handle special cases
    if (colorPart === 'transparent') {
      return { color: 'transparent', shade: null };
    }
    if (colorPart === 'white') {
      return { color: 'white', shade: null };
    }
    if (colorPart === 'black') {
      return { color: 'black', shade: null };
    }
    
    // Handle normal color-shade pattern
    const match = colorPart.match(/^(\w+)-(\d+)$/);
    if (match) {
      return { color: match[1], shade: match[2] };
    }
    
    return { color: null, shade: '500' };
  };

  const { color: currentColor, shade: currentShade } = extractColorInfo(value);

  // Get color hex value from Tailwind class
  const getColorValue = (color: string, shade: string | null) => {
    // Handle special cases
    if (color === 'transparent') return 'transparent';
    if (color === 'white') return '#ffffff';
    if (color === 'black') return '#000000';
    
    // Handle normal colors
    if (shade && TAILWIND_COLOR_VALUES[color]) {
      return TAILWIND_COLOR_VALUES[color]?.[shade] || '#000000';
    }
    return '#000000';
  };

  // Get current color hex value
  const currentColorValue = useMemo(() => {
    if (value.startsWith('#')) return value;
    if (currentColor) {
      return getColorValue(currentColor, currentShade);
    }
    return '#6b7280'; // Default gray
  }, [value, currentColor, currentShade]);

  // Get icon based on type
  const getIcon = () => {
    switch (type) {
      case 'text':
        return <Palette className="w-4 h-4" />;
      case 'background':
        return <Droplet className="w-4 h-4" />;
      case 'border':
        return <div className="w-4 h-4 border-2 border-current rounded" />;
    }
  };

  // Handle color selection
  const handleColorSelect = (color: string, shade: string) => {
    const prefix = type === 'text' ? 'text' : type === 'background' ? 'bg' : 'border';
    const newClass = `${prefix}-${color}-${shade}`;
    
    if (autoSave) {
      // Apply instantly and keep picker open for more changes
      onChange(newClass);
      onAddToRecent?.(newClass);
      // Don't close picker - let user make multiple changes
      // setShowPicker(false);
    } else {
      setSelectedColor(color);
      setSelectedShade(shade);
    }
  };

  // Apply manually selected color
  const applyColor = () => {
    if (selectedColor) {
      const prefix = type === 'text' ? 'text' : type === 'background' ? 'bg' : 'border';
      const newClass = `${prefix}-${selectedColor}-${selectedShade}`;
      onChange(newClass);
      onAddToRecent?.(newClass);
      setShowPicker(false);
      setSelectedColor(null);
    }
  };

  // Handle custom hex color
  const handleCustomHex = () => {
    // User enters 6 hex digits, we prepend #
    if (customHex.match(/^[0-9A-Fa-f]{6}$/)) {
      const hexWithHash = `#${customHex}`;
      onChange(hexWithHash);
      onAddToRecent?.(hexWithHash);
      // Keep picker open for more changes
      setCustomHex('');
    }
  };

  return (
    <div className="space-y-3">
      {/* Header with current selection */}
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-300">
          {getIcon()}
          {label}
        </label>
        {currentColor && (
          <span className="text-xs font-mono text-gray-500 px-2 py-1 bg-gray-800/50 rounded">
            {currentColor}{currentShade ? `-${currentShade}` : ''}
          </span>
        )}
      </div>

      {/* Enhanced Current Color Display */}
      <button
        onClick={() => setShowPicker(!showPicker)}
        className="w-full group relative overflow-hidden rounded-lg border-2 border-gray-700 hover:border-blue-500 transition-all duration-200"
      >
        {/* Color preview with gradient effect */}
        <div className="flex items-center gap-3 p-3 bg-gray-800/50 backdrop-blur-sm">
          <div className="relative">
            {/* Checkerboard background for transparent colors */}
            {currentColorValue === 'transparent' && (
              <div 
                className="absolute inset-0 rounded-lg"
                style={{
                  backgroundImage: 'linear-gradient(45deg, #6b7280 25%, transparent 25%), linear-gradient(-45deg, #6b7280 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #6b7280 75%), linear-gradient(-45deg, transparent 75%, #6b7280 75%)',
                  backgroundSize: '8px 8px',
                  backgroundPosition: '0 0, 0 4px, 4px -4px, -4px 0px'
                }}
              />
            )}
            <div
              className="w-12 h-12 rounded-lg shadow-lg ring-2 ring-gray-600 group-hover:ring-blue-500 transition-all duration-200 group-hover:scale-110 relative"
              style={{ backgroundColor: currentColorValue !== 'transparent' ? currentColorValue : undefined }}
            />
            {/* Small indicator of color type */}
            <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-gray-900 rounded-full flex items-center justify-center border-2 border-gray-700 group-hover:border-blue-500 transition-colors">
              {type === 'text' && <span className="text-[8px]">A</span>}
              {type === 'background' && <Droplet className="w-2.5 h-2.5" />}
              {type === 'border' && <div className="w-2 h-2 border border-current rounded-sm" />}
            </div>
          </div>
          
          <div className="flex-1 text-left">
            <div className="text-sm font-medium text-gray-200">{value}</div>
            <div className="text-xs text-gray-500 mt-0.5">
              {currentColorValue} • Click to change
            </div>
          </div>
          
          <div className="text-gray-500 group-hover:text-blue-400 transition-colors">
            {showPicker ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </div>
        </div>
      </button>

      {/* Enhanced Color Picker Dropdown */}
      {showPicker && (
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-gray-700 rounded-xl shadow-2xl overflow-hidden">
          <div className="max-h-[32rem] overflow-y-auto custom-scrollbar">
            <div className="p-4 space-y-4">
              
              {/* Popular Colors Quick Select */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                    Quick Select
                  </h3>
                  <div className="h-px flex-1 bg-gradient-to-r from-gray-700 to-transparent ml-3" />
                </div>
                <div className="grid grid-cols-4 gap-2">
                  {POPULAR_COLORS.map(({ color, shade, label }) => {
                    const colorValue = getColorValue(color, shade);
                    const isSelected = currentColor === color && currentShade === shade;
                    return (
                      <button
                        key={`${color}-${shade}`}
                        onClick={() => handleColorSelect(color, shade)}
                        className={`group relative p-2 rounded-lg border-2 transition-all duration-200 ${
                          isSelected 
                            ? 'border-blue-500 bg-blue-500/10 scale-95' 
                            : 'border-gray-700 hover:border-gray-600 hover:scale-105'
                        }`}
                        title={label}
                      >
                        <div
                          className="w-full h-8 rounded-md shadow-sm"
                          style={{ backgroundColor: colorValue }}
                        />
                        <div className="text-[10px] text-gray-400 text-center mt-1 truncate">
                          {label}
                        </div>
                        {isSelected && (
                          <div className="absolute -top-1 -right-1 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center">
                            <Check className="w-2.5 h-2.5 text-white" />
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Custom Hex Input */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                    Custom Color
                  </h3>
                  <div className="h-px flex-1 bg-gradient-to-r from-gray-700 to-transparent ml-3" />
                </div>
                <div className="flex gap-2">
                  <div className="relative flex-1 flex items-center">
                    {/* Color preview swatch */}
                    <div 
                      className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 rounded border border-gray-600 shadow-sm"
                      style={{ backgroundColor: customHex.match(/^[0-9A-Fa-f]{6}$/) ? `#${customHex}` : '#1f2937' }}
                    />
                    {/* Static # symbol */}
                    <span className="absolute left-11 top-1/2 -translate-y-1/2 text-gray-400 text-sm font-mono pointer-events-none">
                      #
                    </span>
                    {/* Hex input */}
                    <input
                      ref={colorInputRef}
                      type="text"
                      value={customHex}
                      onChange={(e) => {
                        // Only allow hex characters
                        const value = e.target.value.toUpperCase().replace(/[^0-9A-F]/g, '');
                        setCustomHex(value);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleCustomHex();
                        }
                      }}
                      placeholder="000000"
                      className="w-full px-3 py-2 pl-14 bg-gray-900/50 text-gray-100 text-sm rounded-lg border border-gray-700 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all font-mono"
                      maxLength={6}
                    />
                  </div>
                  <button
                    onClick={handleCustomHex}
                    disabled={!customHex.match(/^[0-9A-Fa-f]{6}$/)}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm rounded-lg font-medium transition-all hover:shadow-lg hover:shadow-blue-500/20"
                  >
                    Apply
                  </button>
                </div>
              </div>

              {/* Color Categories */}
              {Object.entries(COLOR_CATEGORIES).map(([categoryName, colors]) => (
                <div key={categoryName}>
                  <button
                    onClick={() => setExpandedCategory(expandedCategory === categoryName ? null : categoryName)}
                    className="w-full flex items-center justify-between mb-3 group"
                  >
                    <h3 className="text-xs font-semibold text-gray-300 uppercase tracking-wider capitalize">
                      {categoryName}
                    </h3>
                    <div className="flex items-center gap-2">
                      <div className="h-px flex-1 bg-gradient-to-r from-gray-700 to-transparent w-32" />
                      {expandedCategory === categoryName ? (
                        <ChevronUp className="w-4 h-4 text-gray-500 group-hover:text-gray-300" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-gray-500 group-hover:text-gray-300" />
                      )}
                    </div>
                  </button>
                  
                  {expandedCategory === categoryName && (
                    <div className="space-y-3 animate-in slide-in-from-top-2 duration-200">
                      {colors.map((colorName) => (
                        <div key={colorName} className="space-y-2">
                          <div className="text-xs font-medium text-gray-400 capitalize px-1">
                            {colorName}
                          </div>
                          <div className="grid grid-cols-11 gap-1.5">
                            {TAILWIND_COLOR_SHADES.map((shade) => {
                              const colorValue = getColorValue(colorName, shade);
                              const isSelected = currentColor === colorName && currentShade === shade;
                              
                              return (
                                <button
                                  key={shade}
                                  onClick={() => handleColorSelect(colorName, shade)}
                                  className={`relative w-full aspect-square rounded-md transition-all duration-200 ${
                                    isSelected 
                                      ? 'ring-2 ring-blue-500 ring-offset-2 ring-offset-gray-900 scale-110 z-10' 
                                      : 'hover:scale-110 hover:z-10 hover:shadow-lg'
                                  }`}
                                  style={{ backgroundColor: colorValue }}
                                  title={`${colorName}-${shade}`}
                                >
                                  {isSelected && (
                                    <div className="absolute inset-0 flex items-center justify-center">
                                      <div className="w-3 h-3 bg-white rounded-full flex items-center justify-center shadow-lg">
                                        <Check className="w-2 h-2 text-gray-900" strokeWidth={3} />
                                      </div>
                                    </div>
                                  )}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Footer with live preview */}
          <div className="border-t border-gray-700 bg-gray-900/50 backdrop-blur-sm p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className="w-6 h-6 rounded-md border-2 border-gray-600 shadow-sm"
                  style={{ backgroundColor: currentColorValue }}
                />
                <div className="text-xs text-gray-400">
                  Changes apply in real-time
                </div>
              </div>
              <button
                onClick={() => setShowPicker(false)}
                className="px-4 py-1.5 text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all hover:shadow-lg hover:shadow-blue-500/20"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

