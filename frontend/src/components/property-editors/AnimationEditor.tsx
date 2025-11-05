'use client';

import { Zap } from 'lucide-react';

interface AnimationEditorProps {
  transition?: string;
  animation?: string;
  opacity?: string;
  onTransitionChange?: (value: string) => void;
  onAnimationChange?: (value: string) => void;
  onOpacityChange?: (value: string) => void;
}

const TRANSITION_DURATIONS = [
  { value: 'duration-75', label: '75ms' },
  { value: 'duration-100', label: '100ms' },
  { value: 'duration-150', label: '150ms' },
  { value: 'duration-200', label: '200ms' },
  { value: 'duration-300', label: '300ms' },
  { value: 'duration-500', label: '500ms' },
  { value: 'duration-700', label: '700ms' },
  { value: 'duration-1000', label: '1000ms' },
];

export default function AnimationEditor({
  transition = 'duration-300',
  opacity = '100',
  onTransitionChange,
  onOpacityChange,
}: AnimationEditorProps) {
  return (
    <div className="space-y-4">
      {/* Opacity */}
      {onOpacityChange && (
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs font-medium text-gray-400">
            <Zap className="w-3 h-3" />
            Opacity
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={opacity}
            onChange={(e) => onOpacityChange(e.target.value)}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500">
            <span>0%</span>
            <span className="text-gray-300">{opacity}%</span>
            <span>100%</span>
          </div>
        </div>
      )}

      {/* Transition Duration */}
      {onTransitionChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Transition Duration</label>
          <div className="grid grid-cols-4 gap-2">
            {TRANSITION_DURATIONS.map((duration) => (
              <button
                key={duration.value}
                onClick={() => onTransitionChange(duration.value)}
                className={`px-2 py-2 text-xs rounded border transition-colors ${
                  transition === duration.value
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
                }`}
              >
                {duration.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

