'use client';

import { Sparkles } from 'lucide-react';
import { TAILWIND_SHADOWS } from '@/types/property-edit.types';

interface ShadowEditorProps {
  shadow?: string;
  onShadowChange?: (value: string) => void;
}

export default function ShadowEditor({
  shadow = 'shadow-none',
  onShadowChange,
}: ShadowEditorProps) {
  if (!onShadowChange) return null;

  return (
    <div className="space-y-4">
      <label className="flex items-center gap-2 text-xs font-medium text-gray-400">
        <Sparkles className="w-3 h-3" />
        Box Shadow
      </label>

      {/* Shadow Presets */}
      <div className="grid grid-cols-2 gap-3">
        {TAILWIND_SHADOWS.map((shadowPreset) => (
          <button
            key={shadowPreset.value}
            onClick={() => onShadowChange(shadowPreset.value)}
            className={`p-4 rounded border transition-all ${
              shadow === shadowPreset.value
                ? 'bg-blue-600 border-blue-500'
                : 'bg-gray-800 border-gray-700 hover:border-gray-600'
            }`}
          >
            <div
              className={`w-full h-16 bg-gray-700 rounded ${shadowPreset.value} mb-2`}
            />
            <div className="text-xs text-center text-gray-300">
              {shadowPreset.label}
            </div>
          </button>
        ))}
      </div>

      {/* Current Shadow Info */}
      <div className="text-xs text-gray-500 bg-gray-800/50 p-3 rounded border border-gray-700">
        <div className="font-mono">{shadow}</div>
      </div>
    </div>
  );
}

