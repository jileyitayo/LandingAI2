'use client';

import { useState, useRef } from 'react';
import { Palette, Droplet, Check } from 'lucide-react';
import { TAILWIND_COLORS, TAILWIND_COLOR_SHADES } from '@/types/property-edit.types';

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
  const colorInputRef = useRef<HTMLInputElement>(null);

  // Extract color info from Tailwind class
  const extractColorInfo = (tailwindClass: string) => {
    const prefix = type === 'text' ? 'text-' : type === 'background' ? 'bg-' : 'border-';
    const colorPart = tailwindClass.replace(prefix, '');
    const match = colorPart.match(/^(\w+)-(\d+)$/);
    
    if (match) {
      return { color: match[1], shade: match[2] };
    }
    return { color: null, shade: '500' };
  };

  const { color: currentColor, shade: currentShade } = extractColorInfo(value);

  // Get icon based on type
  const getIcon = () => {
    switch (type) {
      case 'text':
        return <Palette className="w-3 h-3" />;
      case 'background':
        return <Droplet className="w-3 h-3" />;
      case 'border':
        return <div className="w-3 h-3 border-2 border-current rounded" />;
    }
  };

  // Get current color display
  const getCurrentColorDisplay = () => {
    if (!currentColor) return '#000000';
    // Simplified color mapping (in real app, use actual Tailwind colors)
    return `var(--${currentColor}-${currentShade})`;
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
    if (customHex.match(/^#[0-9A-Fa-f]{6}$/)) {
      // In a real implementation, we'd convert hex to closest Tailwind color
      // Apply instantly and keep picker open
      onChange(customHex);
      onAddToRecent?.(customHex);
      // Keep picker open for more changes
      setCustomHex('');
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 text-xs font-medium text-gray-400">
          {getIcon()}
          {label}
        </label>
        {!autoSave && selectedColor && (
          <button
            onClick={applyColor}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
          >
            <Check className="w-3 h-3" />
            Apply
          </button>
        )}
      </div>

      {/* Current Color Display */}
      <button
        onClick={() => setShowPicker(!showPicker)}
        className="w-full flex items-center gap-3 p-3 bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-gray-600 rounded transition-colors"
      >
        <div
          className={`w-10 h-10 rounded border-2 border-gray-600 ${value}`}
          style={value.startsWith('#') ? { backgroundColor: value } : undefined}
        />
        <div className="flex-1 text-left">
          <div className="text-sm text-gray-300 font-mono">{value}</div>
          <div className="text-xs text-gray-500">Click to change</div>
        </div>
        <Palette className="w-4 h-4 text-gray-500" />
      </button>

      {/* Color Picker Dropdown */}
      {showPicker && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 max-h-96 overflow-y-auto">
          {/* Recent Colors */}
          {recentColors.length > 0 && (
            <div className="mb-3">
              <div className="text-xs text-gray-400 mb-2">Recent</div>
              <div className="flex flex-wrap gap-2">
                {recentColors.map((color, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      onChange(color);
                      onAddToRecent?.(color);
                      // Keep picker open for more changes
                    }}
                    className={`w-8 h-8 rounded border-2 hover:scale-110 transition-transform ${color}`}
                    title={color}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Custom Hex Input */}
          <div className="mb-3">
            <div className="text-xs text-gray-400 mb-2">Custom Hex</div>
            <div className="flex gap-2">
              <input
                ref={colorInputRef}
                type="text"
                value={customHex}
                onChange={(e) => setCustomHex(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleCustomHex();
                  }
                }}
                placeholder="#000000"
                className="flex-1 px-3 py-2 bg-gray-900 text-gray-100 text-sm rounded border border-gray-700 focus:outline-none focus:border-blue-500"
                maxLength={7}
              />
              <button
                onClick={handleCustomHex}
                disabled={!customHex.match(/^#[0-9A-Fa-f]{6}$/)}
                className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white text-sm rounded transition-colors"
              >
                Apply
              </button>
            </div>
          </div>

          {/* Tailwind Color Palette */}
          <div className="text-xs text-gray-400 mb-2">Tailwind Colors</div>
          <div className="space-y-3">
            {TAILWIND_COLORS.map((colorName) => (
              <div key={colorName}>
                <div className="text-xs text-gray-500 mb-1 capitalize">{colorName}</div>
                <div className="grid grid-cols-11 gap-1">
                  {TAILWIND_COLOR_SHADES.map((shade) => {
                    const prefix = type === 'text' ? 'text' : type === 'background' ? 'bg' : 'border';
                    const colorClass = `${prefix}-${colorName}-${shade}`;
                    const isSelected = currentColor === colorName && currentShade === shade;
                    
                    return (
                      <button
                        key={shade}
                        onClick={() => handleColorSelect(colorName, shade)}
                        className={`w-6 h-6 rounded border-2 hover:scale-110 transition-transform ${colorClass} ${
                          isSelected ? 'ring-2 ring-blue-500 ring-offset-2 ring-offset-gray-800' : 'border-gray-600'
                        }`}
                        title={`${colorName}-${shade}`}
                      />
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="mt-3 pt-3 border-t border-gray-700 flex justify-between items-center gap-2">
            <div className="text-xs text-gray-400">
              Click colors to apply instantly
            </div>
            <button
              onClick={() => setShowPicker(false)}
              className="px-4 py-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

