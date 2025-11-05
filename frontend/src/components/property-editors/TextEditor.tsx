'use client';

import { useState, useEffect, useRef } from 'react';
import { Type, Check } from 'lucide-react';

interface TextEditorProps {
  value: string;
  onChange: (value: string) => void;
  maxLength?: number;
  minLength?: number;
  placeholder?: string;
  autoSave?: boolean;
  onSave?: () => void;
}

export default function TextEditor({
  value,
  onChange,
  maxLength = 500,
  minLength = 0,
  placeholder = 'Enter text...',
  autoSave = true,
  onSave,
}: TextEditorProps) {
  const [localValue, setLocalValue] = useState(value);
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Update local value when prop changes
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [localValue]);

  // Auto-save on blur if enabled
  const handleBlur = () => {
    setIsFocused(false);
    if (autoSave && localValue !== value) {
      onChange(localValue);
      onSave?.();
    }
  };

  // Manual save with Enter key (Ctrl+Enter for multiline)
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      e.preventDefault();
      handleBlur();
      textareaRef.current?.blur();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    if (maxLength && newValue.length > maxLength) {
      return; // Don't allow exceeding max length
    }
    setLocalValue(newValue);
  };

  const characterCount = localValue.length;
  const isValid = characterCount >= minLength && characterCount <= maxLength;
  const hasChanges = localValue !== value;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 text-xs font-medium text-gray-400">
          <Type className="w-3 h-3" />
          Text Content
        </label>
        {hasChanges && !autoSave && (
          <button
            onClick={handleBlur}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
          >
            <Check className="w-3 h-3" />
            Apply
          </button>
        )}
      </div>

      <div className="relative">
        <textarea
          ref={textareaRef}
          value={localValue}
          onChange={handleChange}
          onFocus={() => setIsFocused(true)}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className={`w-full px-3 py-2 bg-gray-800 text-gray-100 text-sm rounded border resize-none focus:outline-none focus:ring-2 transition-all ${
            isFocused
              ? 'border-blue-500 ring-blue-500/50'
              : hasChanges
              ? 'border-yellow-500'
              : 'border-gray-700'
          }`}
          style={{
            minHeight: '60px',
            maxHeight: '200px',
          }}
          rows={3}
        />
      </div>

      <div className="flex items-center justify-between text-xs">
        <div className={`${isValid ? 'text-gray-500' : 'text-red-400'}`}>
          {characterCount} / {maxLength} characters
          {minLength > 0 && characterCount < minLength && ` (min: ${minLength})`}
        </div>
        {autoSave && hasChanges && (
          <div className="text-yellow-400">Press Ctrl+Enter or click outside to save</div>
        )}
      </div>

      {!autoSave && hasChanges && (
        <div className="text-xs text-gray-400 bg-gray-800/50 p-2 rounded border border-gray-700">
          💡 Click "Apply" to save your changes
        </div>
      )}
    </div>
  );
}

