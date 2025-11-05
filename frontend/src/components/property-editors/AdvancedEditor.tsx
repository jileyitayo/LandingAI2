'use client';

import { useState } from 'react';
import { Code, Plus, X } from 'lucide-react';

interface AdvancedEditorProps {
  customClasses?: string;
  dataAttributes?: Record<string, string>;
  onCustomClassesChange?: (value: string) => void;
  onDataAttributeAdd?: (key: string, value: string) => void;
  onDataAttributeRemove?: (key: string) => void;
}

export default function AdvancedEditor({
  customClasses = '',
  dataAttributes = {},
  onCustomClassesChange,
  onDataAttributeAdd,
  onDataAttributeRemove,
}: AdvancedEditorProps) {
  const [newAttrKey, setNewAttrKey] = useState('');
  const [newAttrValue, setNewAttrValue] = useState('');

  const handleAddAttribute = () => {
    if (newAttrKey && newAttrValue && onDataAttributeAdd) {
      onDataAttributeAdd(newAttrKey, newAttrValue);
      setNewAttrKey('');
      setNewAttrValue('');
    }
  };

  return (
    <div className="space-y-4">
      {/* Custom CSS Classes */}
      {onCustomClassesChange && (
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs font-medium text-gray-400">
            <Code className="w-3 h-3" />
            Custom CSS Classes
          </label>
          <textarea
            value={customClasses}
            onChange={(e) => onCustomClassesChange(e.target.value)}
            placeholder="e.g., custom-class another-class"
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-300 focus:outline-none focus:border-blue-500 font-mono"
            rows={3}
          />
          <div className="text-xs text-gray-500">
            Add custom Tailwind classes separated by spaces
          </div>
        </div>
      )}

      {/* Data Attributes */}
      {(onDataAttributeAdd || onDataAttributeRemove) && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Data Attributes</label>
          
          {/* Existing Attributes */}
          {Object.keys(dataAttributes).length > 0 && (
            <div className="space-y-2 mb-3">
              {Object.entries(dataAttributes).map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-center gap-2 p-2 bg-gray-800 rounded border border-gray-700"
                >
                  <div className="flex-1 font-mono text-xs text-gray-300">
                    <span className="text-blue-400">{key}</span>=
                    <span className="text-green-400">"{value}"</span>
                  </div>
                  {onDataAttributeRemove && (
                    <button
                      onClick={() => onDataAttributeRemove(key)}
                      className="text-red-400 hover:text-red-300 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Add New Attribute */}
          {onDataAttributeAdd && (
            <div className="space-y-2 p-3 bg-gray-800/50 rounded border border-gray-700">
              <div className="text-xs text-gray-400 mb-2">Add New Attribute</div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newAttrKey}
                  onChange={(e) => setNewAttrKey(e.target.value)}
                  placeholder="data-name"
                  className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-300 focus:outline-none focus:border-blue-500"
                />
                <input
                  type="text"
                  value={newAttrValue}
                  onChange={(e) => setNewAttrValue(e.target.value)}
                  placeholder="value"
                  className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-300 focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={handleAddAttribute}
                  disabled={!newAttrKey || !newAttrValue}
                  className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded transition-colors"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Warning */}
      <div className="text-xs text-yellow-500 bg-yellow-900/20 border border-yellow-700/50 p-3 rounded">
        ⚠️ Advanced: Changes here may affect functionality. Use with caution.
      </div>
    </div>
  );
}

